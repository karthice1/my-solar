import asyncio
import os
import re
import json
import csv
import io
import math
import glob
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Request, Query, HTTPException, UploadFile, File, Header, Body
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from tneb_tool import main_async, BASE_URL
from quotation.settings_manager import (
    load_owner_settings,
    save_owner_settings,
    reset_owner_settings,
    verify_owner_pin,
    generate_owner_token,
    verify_owner_token
)
from quotation.quotation_builder import build_initial_quotation, recalculate_quotation
from quotation.quotation_history import (
    save_quotation,
    get_quotation,
    list_quotations,
    update_status,
    generate_next_quotation_no,
    get_quotation_versions
)
from quotation.pdf_generator import generate_quotation_pdf, OUTPUT_PDF_DIR

app = FastAPI(
    title="TNEB Account Extractor & Billing Intelligence",
    description="Standalone Portal Automation Tool for TNEB Connection Extraction, Ledger Analysis & Auto-Cleanup",
    version="1.0.0"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUT_PDF_DIR, exist_ok=True)

templates = Jinja2Templates(directory=TEMPLATES_DIR)
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")
app.mount("/generated_quotations", StaticFiles(directory=OUTPUT_PDF_DIR), name="generated_quotations")

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    """Renders the main modern interactive dashboard."""
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/api/stream")
async def stream_extraction(
    consumer_no: str = Query(..., description="TNEB 12-digit consumer number"),
    user_id: str = Query(..., description="TNEB Portal User ID"),
    password: str = Query(..., description="TNEB Portal Password"),
    delete_after: bool = Query(True, description="Auto-delete consumer from portal after extraction"),
    headed: bool = Query(False, description="Run browser in visible mode")
):
    """Server-Sent Events (SSE) streaming live step progress and data."""
    clean_no = re.sub(r'[^0-9]', '', consumer_no)
    if not clean_no:
        raise HTTPException(status_code=400, detail="Invalid consumer number. Must contain digits.")
        
    clean_user = user_id.strip()
    if not clean_user:
        raise HTTPException(status_code=400, detail="User ID is required.")
        
    clean_pass = password.strip()
    if not clean_pass:
        raise HTTPException(status_code=400, detail="Password is required.")

    async def event_generator():
        queue = asyncio.Queue()

        async def step_callback(step: str, message: str, status: str = "info", data: Any = None):
            payload = {
                "step": step,
                "message": message,
                "status": status,
                "data": data,
                "time": datetime.now().strftime("%H:%M:%S")
            }
            await queue.put(payload)

        # Run extraction task in asyncio background
        task = asyncio.create_task(
            main_async(
                consumer_no=clean_no,
                user_id=clean_user,
                password=clean_pass,
                headless=not headed,
                delete_after=delete_after,
                callback=step_callback
            )
        )

        while True:
            try:
                item = await asyncio.wait_for(queue.get(), timeout=0.6)
                yield f"data: {json.dumps(item)}\n\n"
                if item.get("status") in ["done", "error"]:
                    break
            except asyncio.TimeoutError:
                if task.done():
                    # Drain any final items in queue
                    while not queue.empty():
                        item = queue.get_nowait()
                        yield f"data: {json.dumps(item)}\n\n"
                    # Check if exception occurred
                    exc = task.exception()
                    if exc:
                        err_payload = {
                            "step": "error",
                            "message": str(exc),
                            "status": "error",
                            "time": datetime.now().strftime("%H:%M:%S")
                        }
                        yield f"data: {json.dumps(err_payload)}\n\n"
                    break
                # Keep-alive comment
                yield ": keep-alive\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.get("/api/reports")
async def list_reports():
    """Lists all previously harvested reports available on disk."""
    report_files = glob.glob(os.path.join(BASE_DIR, "tneb_report_*.json"))
    results = []
    for fpath in report_files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
                c_no = data.get("consumer_no", "")
                sa = data.get("solar_analysis", {})
                results.append({
                    "consumer_no": c_no,
                    "consumer_name": data.get("consumer_name", ""),
                    "tariff": data.get("tariff_code", ""),
                    "load": data.get("sanctioned_load", ""),
                    "phase": data.get("phase", ""),
                    "cycles_count": len(data.get("billing_cycles", [])),
                    "due_amount": data.get("dues", {}).get("amount", 0.0),
                    "has_dues": data.get("dues", {}).get("has_dues", False),
                    "solar_capacity_kw": sa.get("solar_capacity_required_kw", 0.0),
                    "solar_total_units": sa.get("total_6_cycles_units", 0.0),
                    "file_date": datetime.fromtimestamp(os.path.getmtime(fpath)).strftime("%Y-%m-%d %H:%M"),
                    "has_screenshot": os.path.exists(os.path.join(BASE_DIR, f"tneb_detail_{c_no}.png"))
                })
        except Exception:
            pass
            
    # Sort by file_date descending
    results.sort(key=lambda x: x["file_date"], reverse=True)
    return {"reports": results}

@app.get("/api/reports/{consumer_no}")
async def get_report_data(consumer_no: str):
    """Retrieves full JSON details for a specific consumer."""
    clean_no = re.sub(r'[^0-9]', '', consumer_no)
    fpath = os.path.join(BASE_DIR, f"tneb_report_{clean_no}.json")
    if not os.path.exists(fpath):
        raise HTTPException(status_code=404, detail=f"No report found for consumer {clean_no}")
    with open(fpath, "r", encoding="utf-8") as f:
        return json.load(f)

@app.get("/api/screenshots/{consumer_no}")
async def get_screenshot(consumer_no: str):
    """Serves the captured high-res full page audit snapshot."""
    clean_no = re.sub(r'[^0-9]', '', consumer_no)
    png_path = os.path.join(BASE_DIR, f"tneb_detail_{clean_no}.png")
    if not os.path.exists(png_path):
        raise HTTPException(status_code=404, detail="Screenshot not found")
    return FileResponse(png_path, media_type="image/png")

@app.get("/api/export/{consumer_no}/csv")
async def export_csv(consumer_no: str):
    """Generates and downloads a clean CSV ledger file."""
    clean_no = re.sub(r'[^0-9]', '', consumer_no)
    fpath = os.path.join(BASE_DIR, f"tneb_report_{clean_no}.json")
    if not os.path.exists(fpath):
        raise HTTPException(status_code=404, detail="Report not found")
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Assessment Date", "Entry Date", "Status", "KWH Reading", "Units Consumed (kWh)",
        "Recorded Demand (kW)", "CC Charges (Rs)", "Amount Paid (Rs)", "Payment Date", "Receipt No"
    ])
    for c in data.get("billing_cycles", []):
        writer.writerow([
            c.get("assessment_date", ""),
            c.get("entry_date", ""),
            c.get("status", ""),
            c.get("kwh_reading", 0.0),
            c.get("units_consumed", 0.0),
            c.get("recorded_demand", 0.0),
            c.get("cc_charges", 0.0),
            c.get("amount_paid", 0.0),
            c.get("payment_date", ""),
            c.get("receipt_no", "")
        ])
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=tneb_ledger_{clean_no}.csv"}
    )

@app.get("/api/export/{consumer_no}/markdown")
async def export_markdown(consumer_no: str):
    """Downloads the official Markdown report."""
    clean_no = re.sub(r'[^0-9]', '', consumer_no)
    md_path = os.path.join(BASE_DIR, f"tneb_report_{clean_no}.md")
    if not os.path.exists(md_path):
        raise HTTPException(status_code=404, detail="Markdown report not found")
    return FileResponse(
        md_path,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=tneb_report_{clean_no}.md"}
    )

# ======================================================================
# MODULE A & SECURITY: OWNER QUOTATION SETTINGS ENDPOINTS
# ======================================================================

@app.post("/api/settings/auth")
async def authenticate_owner(payload: Dict[str, Any] = Body(...)):
    """Authenticates the business owner/admin via PIN and returns a session token."""
    pin = str(payload.get("pin") or "").strip()
    if not pin:
        raise HTTPException(status_code=400, detail="Owner PIN cannot be empty.")
    if verify_owner_pin(pin):
        token = generate_owner_token(pin)
        return {"authenticated": True, "token": token, "message": "Owner authentication successful."}
    raise HTTPException(status_code=401, detail="Invalid Owner/Admin PIN.")

@app.get("/api/settings")
async def get_settings(x_owner_token: Optional[str] = Header(None)):
    """
    Returns owner quotation configuration.
    If authorized with owner token, returns full commercial pricing & admin settings.
    If unauthorized, returns public branding & panel configuration without sensitive pricing.
    """
    settings = load_owner_settings()
    is_admin = verify_owner_token(x_owner_token) if x_owner_token else False
    if not is_admin:
        # Mask administrative PIN and sensitive markup
        safe_copy = json.loads(json.dumps(settings))
        safe_copy.pop("admin_pin", None)
        return {"settings": safe_copy, "is_admin": False}
    return {"settings": settings, "is_admin": True}

@app.post("/api/settings")
async def update_settings(
    settings: Dict[str, Any] = Body(...),
    x_owner_token: Optional[str] = Header(None)
):
    """Saves updated owner quotation settings persistently. Requires owner token."""
    if not x_owner_token or not verify_owner_token(x_owner_token):
        raise HTTPException(status_code=403, detail="Unauthorized. Owner authentication required to modify settings.")
    try:
        saved = save_owner_settings(settings)
        return {"success": True, "settings": saved, "message": "Owner settings saved persistently."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/settings/reset")
async def reset_settings(x_owner_token: Optional[str] = Header(None)):
    """Resets owner settings back to system factory defaults."""
    if not x_owner_token or not verify_owner_token(x_owner_token):
        raise HTTPException(status_code=403, detail="Unauthorized. Owner authentication required.")
    reset_data = reset_owner_settings()
    return {"success": True, "settings": reset_data, "message": "Settings reset to defaults."}

@app.post("/api/settings/logo")
async def upload_logo(
    file: UploadFile = File(...),
    x_owner_token: Optional[str] = Header(None)
):
    """Uploads company logo with MIME & size validation, updating owner branding."""
    if not x_owner_token or not verify_owner_token(x_owner_token):
        raise HTTPException(status_code=403, detail="Unauthorized. Owner authentication required.")
    
    # Validate extension & content type
    allowed = {".png", ".jpg", ".jpeg", ".svg", ".webp"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {', '.join(allowed)}")

    content = await file.read()
    if len(content) > 2 * 1024 * 1024:  # 2MB max
        raise HTTPException(status_code=400, detail="Logo file size exceeds 2MB limit.")

    clean_name = f"company_logo{ext}"
    dest_path = os.path.join(UPLOADS_DIR, clean_name)
    with open(dest_path, "wb") as f:
        f.write(content)

    logo_url = f"/uploads/{clean_name}"
    curr = load_owner_settings()
    curr["branding"]["logo_url"] = logo_url
    save_owner_settings(curr)

    return {"success": True, "logo_url": logo_url, "message": "Company logo uploaded successfully."}


# ======================================================================
# MODULE C, D & E: INTERACTIVE QUOTATION GENERATION & RECALCULATION
# ======================================================================

@app.get("/api/quotation/generate/{consumer_no}")
async def generate_quotation_for_consumer(consumer_no: str):
    """
    Generates an initial customer-specific solar quotation using verified TNEB data
    and persistent owner settings.
    """
    clean_no = re.sub(r'[^0-9]', '', consumer_no)
    report_file = os.path.join(BASE_DIR, f"tneb_report_{clean_no}.json")
    if not os.path.exists(report_file):
        raise HTTPException(
            status_code=404,
            detail=f"No verified TNEB report found for consumer {clean_no}. Please extract consumer data first."
        )

    with open(report_file, "r", encoding="utf-8") as f:
        tneb_data = json.load(f)

    q_no = generate_next_quotation_no()
    quotation = build_initial_quotation(tneb_data, quotation_no=q_no)
    return quotation

@app.post("/api/quotation/recalculate")
async def api_recalculate_quotation(payload: Dict[str, Any] = Body(...)):
    """
    Instantly recalculates all dependent technical, commercial and financial values
    when a salesperson modifies permitted customer fields.
    """
    quotation = payload.get("quotation")
    overrides = payload.get("overrides", {})
    if not quotation:
        raise HTTPException(status_code=400, detail="Missing quotation payload.")

    updated = recalculate_quotation(quotation, overrides)
    return updated

@app.post("/api/quotation/save")
async def api_save_quotation(payload: Dict[str, Any] = Body(...)):
    """
    Saves a quotation draft or finalized version into SQLite history.
    If status is 'Finalized', automatically compiles the PDF.
    """
    quotation = payload.get("quotation")
    status = payload.get("status", "Draft")
    if not quotation:
        raise HTTPException(status_code=400, detail="Missing quotation payload.")

    if status == "Finalized" and not quotation.get("pdf_path"):
        try:
            pdf_path = await generate_quotation_pdf(quotation)
            quotation["pdf_path"] = pdf_path
        except Exception as e:
            print(f"[QuotationSave] Error generating PDF during finalize: {e}")

    saved = save_quotation(quotation, status=status)
    return {"success": True, "quotation": saved, "message": f"Quotation saved as {status}."}

@app.post("/api/quotation/pdf")
async def api_generate_pdf(payload: Dict[str, Any] = Body(...)):
    """
    Generates a 5-page pixel-perfect PDF quotation using Playwright Chromium.
    Returns the downloadable URL.
    """
    quotation = payload.get("quotation")
    if not quotation:
        raise HTTPException(status_code=400, detail="Missing quotation payload.")

    try:
        pdf_path = await generate_quotation_pdf(quotation)
        save_quotation(quotation, status=quotation.get("status", "Draft"))
        q_no_slug = re.sub(r'[^A-Za-z0-9]', '_', quotation.get("quotation_no", "DRAFT"))
        return {
            "success": True,
            "pdf_path": pdf_path,
            "pdf_url": f"/api/quotations/{q_no_slug}/download",
            "message": "Quotation PDF generated successfully."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")


# ======================================================================
# MODULE G: QUOTATION HISTORY & VERSION CONTROL ENDPOINTS
# ======================================================================

@app.get("/api/quotations")
async def api_list_quotations(consumer_no: Optional[str] = Query(None)):
    """Retrieves all saved quotations with optional filtering by consumer number."""
    rows = list_quotations(consumer_no=consumer_no)
    return {"quotations": rows}

@app.get("/api/quotations/{quotation_no:path}/download")
async def download_quotation_pdf(quotation_no: str):
    """Downloads or serves the generated quotation PDF."""
    # Find matching PDF
    clean_no = re.sub(r'[^A-Za-z0-9]', '_', quotation_no)
    candidate_paths = [
        os.path.join(OUTPUT_PDF_DIR, f"quotation_{clean_no}.pdf"),
        os.path.join(OUTPUT_PDF_DIR, f"{clean_no}.pdf"),
    ]
    
    # Check SQLite record first
    q_data = get_quotation(quotation_no)
    if q_data and q_data.get("pdf_path") and os.path.exists(q_data["pdf_path"]):
        candidate_paths.insert(0, q_data["pdf_path"])

    for p in candidate_paths:
        if os.path.exists(p):
            return FileResponse(
                p,
                media_type="application/pdf",
                filename=f"Solar_Quotation_{clean_no}.pdf"
            )

    raise HTTPException(status_code=404, detail=f"PDF not found for quotation {quotation_no}. Please generate it first.")


# ======================================================================
# MODULE H: STRUCTURAL INTEGRATION ENDPOINTS (PHASE 1.3)
# ======================================================================

def verify_structural_auth(
    x_owner_token: Optional[str] = Header(None)
) -> bool:
    """
    Enforces authentication for structural administrative, read, and calculation endpoints.
    Accepts token strictly via 'X-Owner-Token' HTTP header. Query parameters are rejected.
    Raises 401 if missing, 403 if invalid.
    """
    if not x_owner_token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Missing X-Owner-Token header."
        )
    if not verify_owner_token(x_owner_token):
        raise HTTPException(
            status_code=403,
            detail="Forbidden. Invalid or expired owner token."
        )
    return True


@app.post("/api/quotations/{quotation_no:path}/structural")
async def api_attach_structural_assessment(
    quotation_no: str,
    mounting_system: Optional[str] = Query(None),
    payload: Optional[Dict[str, Any]] = Body(None),
    x_owner_token: Optional[str] = Header(None),
):
    """
    Associates a structural mounting-system assessment with an existing solar quotation.
    Coordinates project creation, input mapping, and preliminary calculation execution
    without altering solar capacity, panel count, or quotation pricing.
    """
    verify_structural_auth(x_owner_token=x_owner_token)
    from structural.integration import STRUCTURAL_BRIDGE
    if not STRUCTURAL_BRIDGE:
        raise HTTPException(status_code=503, detail="Structural calculation subsystem unavailable.")

    # 1. Fetch source quotation
    q_data = get_quotation(quotation_no)
    if not q_data:
        raise HTTPException(status_code=404, detail=f"Quotation {quotation_no} not found.")

    body_payload = payload or {}
    chosen_system = body_payload.get("mounting_system") or mounting_system or "A"
    site_inputs = body_payload.get("site_inputs")
    roof_inputs = body_payload.get("roof_inputs")
    execute_run = body_payload.get("execute_run", True)

    try:
        # Link / create project
        proj, created = STRUCTURAL_BRIDGE.create_or_get_project_for_quotation(
            quotation_data=q_data,
            mounting_system=chosen_system,
            site_inputs=site_inputs,
            roof_inputs=roof_inputs,
        )

        project_id = proj["project_id"]

        if execute_run:
            assessment_summary = STRUCTURAL_BRIDGE.execute_structural_assessment(
                quotation_no=quotation_no,
                walkway_width_m=float(body_payload.get("walkway_width_m", 0.80)),
                ballast_weight_kn_per_m2=float(body_payload.get("ballast_weight_kn_per_m2", 0.75)),
                friction_coeff_mu=float(body_payload.get("friction_coeff_mu", 0.40)),
            )
        else:
            completeness = STRUCTURAL_BRIDGE.assess_input_completeness(project_id)
            assessment_summary = {
                "quotation_no": quotation_no,
                "project_id": project_id,
                "mounting_system": proj["mounting_system"],
                "requested": True,
                "status": "INPUTS_PENDING" if not completeness["is_complete"] else "INPUTS_CONFIGURED",
                "input_completeness": completeness["status"],
                "missing_inputs": completeness["missing"],
                "approval_status": "BLOCKED_BY_ENGINEERING_HOLDS",
            }

        # Embed into quotation history safely
        updated_quotation = STRUCTURAL_BRIDGE.embed_assessment_in_quotation(q_data, assessment_summary)
        save_quotation(updated_quotation, status=q_data.get("status", "Draft"))

        return {
            "success": True,
            "project_id": project_id,
            "created": created,
            "structural_assessment": assessment_summary,
            "message": "Structural assessment successfully integrated with quotation."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to integrate structural assessment: {e}")


@app.get("/api/quotations/{quotation_no:path}/structural")
async def api_get_structural_assessment(
    quotation_no: str,
    x_owner_token: Optional[str] = Header(None),
):
    """Retrieves current structural assessment summary for a quotation."""
    verify_structural_auth(x_owner_token=x_owner_token)
    from structural.integration import STRUCTURAL_BRIDGE
    from structural.holds import MASTER_VERIFICATION_REGISTER
    if not STRUCTURAL_BRIDGE:
        raise HTTPException(status_code=503, detail="Structural calculation subsystem unavailable.")

    link = STRUCTURAL_BRIDGE.db.get_link_by_quotation(quotation_no)
    if not link:
        return {"requested": False, "status": "NOT_REQUESTED", "message": "No structural assessment requested."}

    project_id = link["project_id"]
    completeness = STRUCTURAL_BRIDGE.assess_input_completeness(project_id)
    latest_run = STRUCTURAL_BRIDGE.db.get_latest_run_for_project(project_id)
    active_holds = MASTER_VERIFICATION_REGISTER.get_active_holds_for_system(link["mounting_system"])

    return {
        "quotation_no": quotation_no,
        "project_id": project_id,
        "mounting_system": link["mounting_system"],
        "requested": True,
        "input_completeness": completeness["status"],
        "missing_inputs": completeness["missing"],
        "latest_run": latest_run,
        "active_holds_count": len(active_holds),
        "active_holds": [h.hold_id for h in active_holds],
        "can_approve_for_construction": False,
        "watermark": "PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION",
        "approval_status": "BLOCKED_BY_ENGINEERING_HOLDS",
    }


@app.get("/api/quotations/{quotation_no:path}/structural/report")
async def api_get_structural_report(
    quotation_no: str,
    x_owner_token: Optional[str] = Header(None),
):
    """Serves the standalone preliminary structural assessment markdown report."""
    verify_structural_auth(x_owner_token=x_owner_token)
    from structural.integration import STRUCTURAL_BRIDGE
    if not STRUCTURAL_BRIDGE:
        raise HTTPException(status_code=503, detail="Structural calculation subsystem unavailable.")

    link = STRUCTURAL_BRIDGE.db.get_link_by_quotation(quotation_no)
    if not link:
        raise HTTPException(status_code=404, detail="No structural assessment linked to this quotation.")

    project_id = link["project_id"]
    try:
        report_md = STRUCTURAL_BRIDGE.generate_structural_assessment_report(project_id, quotation_no=quotation_no)
        clean_no = re.sub(r'[^A-Za-z0-9]', '_', quotation_no)
        return StreamingResponse(
            io.BytesIO(report_md.encode("utf-8")),
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=Structural_Assessment_{clean_no}.md"}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/quotations/{quotation_no:path}/structural/dxf")
async def api_download_structural_dxf(
    quotation_no: str,
    require_approved: bool = Query(False, description="Request approved for construction drawing (blocked while holds active)"),
    x_owner_token: Optional[str] = Header(None),
):
    """Generates and serves the DXF CAD drawing for the quotation with strict hold gate enforcement."""
    verify_structural_auth(x_owner_token=x_owner_token)
    from structural.integration import STRUCTURAL_BRIDGE
    from structural.holds import MASTER_VERIFICATION_REGISTER
    if not STRUCTURAL_BRIDGE:
        raise HTTPException(status_code=503, detail="Structural calculation subsystem unavailable.")

    link = STRUCTURAL_BRIDGE.db.get_link_by_quotation(quotation_no)
    if not link:
        raise HTTPException(status_code=404, detail="No structural assessment linked to this quotation.")

    if require_approved and not MASTER_VERIFICATION_REGISTER.can_label_approved_for_construction(link["mounting_system"]):
        active_holds = MASTER_VERIFICATION_REGISTER.get_active_holds_for_system(link["mounting_system"])
        raise HTTPException(
            status_code=403,
            detail=(
                f"Approved for Construction (AFC) drawing export is strictly forbidden: "
                f"{len(active_holds)} active verification hold(s) remain enforced for {link['mounting_system']}."
            )
        )

    project_id = link["project_id"]
    clean_no = re.sub(r'[^A-Za-z0-9]', '_', quotation_no)
    out_dir = getattr(STRUCTURAL_BRIDGE, "drawing_output_dir", None) or os.path.join(BASE_DIR, "generated_drawings")
    os.makedirs(out_dir, exist_ok=True)
    dxf_path = os.path.join(out_dir, f"Structural_Layout_{clean_no}.dxf")

    try:
        dxf_file = STRUCTURAL_BRIDGE.generate_structural_dxf(
            project_id,
            output_path=dxf_path,
            require_approved=require_approved
        )
        return FileResponse(
            dxf_file,
            media_type="application/dxf",
            filename=f"Structural_Layout_{clean_no}.dxf"
        )
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"DXF generation failed: {e}")


# ======================================================================
# MODULE I: STRUCTURAL PROJECT & WEB UI API ENDPOINTS (PHASE 1.4)
# ======================================================================

@app.get("/api/structural/projects")
async def api_list_structural_projects(
    q: Optional[str] = Query(None, description="Search term for project id, name, client, or quotation"),
    system: Optional[str] = Query(None, description="Filter by mounting system A, B, C, D"),
    status: Optional[str] = Query(None, description="Filter by calculation status (PASS, FAIL, etc.)"),
    completeness: Optional[str] = Query(None, description="Filter by completeness (COMPLETE, INCOMPLETE)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    x_owner_token: Optional[str] = Header(None),
):
    """Lists structural projects with rich search, filters, pagination, and status indicators."""
    verify_structural_auth(x_owner_token=x_owner_token)
    from structural.integration import STRUCTURAL_BRIDGE
    from structural.holds import MASTER_VERIFICATION_REGISTER
    if not STRUCTURAL_BRIDGE:
        raise HTTPException(status_code=503, detail="Structural calculation subsystem unavailable.")

    all_projs = STRUCTURAL_BRIDGE.db.list_projects()
    enriched = []

    for p in all_projs:
        pid = p["project_id"]
        link = STRUCTURAL_BRIDGE.db.get_link_by_project(pid)
        comp = STRUCTURAL_BRIDGE.assess_input_completeness(pid)
        latest_run = STRUCTURAL_BRIDGE.db.get_latest_run_for_project(pid)
        holds = MASTER_VERIFICATION_REGISTER.get_active_holds_for_system(p["mounting_system"])

        item = {
            "project_id": pid,
            "name": p.get("name", ""),
            "client_name": p.get("client_name", ""),
            "site_location": p.get("site_location", ""),
            "mounting_system": p.get("mounting_system", ""),
            "description": p.get("description", ""),
            "status": p.get("status", "DRAFT"),
            "created_at": p.get("created_at", ""),
            "updated_at": p.get("updated_at", ""),
            "associated_quotation_no": link["quotation_no"] if link else None,
            "input_completeness": comp,
            "latest_run": {
                "run_id": latest_run["run_id"],
                "status": latest_run["status"],
                "max_unity_ratio": latest_run["max_unity_ratio"],
                "governing_check": latest_run["governing_check"],
                "created_at": latest_run["created_at"],
            } if latest_run else None,
            "active_holds_count": len(holds),
            "drawing_available": latest_run is not None,
            "approval_status": "BLOCKED_BY_ENGINEERING_HOLDS",
            "watermark": "PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION",
        }

        # Apply Filters
        if q:
            term = q.strip().lower()
            text_corpus = f"{pid} {item['name']} {item['client_name']} {item['site_location']} {item['associated_quotation_no'] or ''}".lower()
            if term not in text_corpus:
                continue

        if system:
            sys_term = system.strip().upper()
            if sys_term not in item["mounting_system"].upper():
                continue

        if status:
            st_term = status.strip().upper()
            run_st = item["latest_run"]["status"].upper() if item["latest_run"] else "NOT_RUN"
            if st_term not in run_st:
                continue

        if completeness:
            c_term = completeness.strip().upper()
            if c_term != item["input_completeness"]["status"].upper():
                continue

        enriched.append(item)

    total_count = len(enriched)
    paginated = enriched[offset:offset + limit]

    return {
        "projects": paginated,
        "total": total_count,
        "offset": offset,
        "limit": limit,
        "governance": {
            "status": "ENGINEERING VERIFICATION PENDING",
            "active_holds": 12,
            "afc_status": "BLOCKED",
            "watermark": "PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION",
        }
    }


@app.post("/api/structural/projects")
async def api_create_structural_project(
    payload: Dict[str, Any] = Body(...),
    x_owner_token: Optional[str] = Header(None),
):
    """Creates a new structural project and optionally associates an existing quotation."""
    verify_structural_auth(x_owner_token=x_owner_token)
    from structural.integration import STRUCTURAL_BRIDGE
    if not STRUCTURAL_BRIDGE:
        raise HTTPException(status_code=503, detail="Structural calculation subsystem unavailable.")

    name = payload.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Project name is required.")

    sys_input = payload.get("mounting_system", "A")
    try:
        resolved_sys = STRUCTURAL_BRIDGE.resolve_mounting_system(sys_input)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    custom_id = payload.get("project_id") or payload.get("project_code")
    if custom_id:
        pid = re.sub(r'[^A-Za-z0-9-_]', '', custom_id).strip()
    else:
        clean_name = re.sub(r'[^A-Za-z0-9]', '-', name).strip('-')
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        pid = f"RS-STR-{clean_name[:16]}-{ts[-6:]}"

    client_name = payload.get("client_name", "")
    site_location = payload.get("site_location", "")
    description = payload.get("description", "")
    quotation_no = payload.get("quotation_no")

    if quotation_no:
        q_data = get_quotation(quotation_no)
        if not q_data:
            raise HTTPException(status_code=404, detail=f"Quotation '{quotation_no}' not found.")
    else:
        q_data = None

    project_created = False
    try:
        proj = STRUCTURAL_BRIDGE.db.create_project(
            project_id=pid,
            name=name,
            mounting_system=resolved_sys,
            client_name=client_name,
            site_location=site_location,
            description=description,
        )
        project_created = True

        if quotation_no and q_data:
            STRUCTURAL_BRIDGE.db.link_quotation_project(
                quotation_no=quotation_no,
                project_id=pid,
                consumer_no=str(q_data.get("consumer_no") or "ANONYMOUS"),
                mounting_system=resolved_sys,
                assessment_requested=True,
            )

        # Apply standard section preset if requested
        if payload.get("auto_preset", True):
            STRUCTURAL_BRIDGE._apply_standard_sections_preset(pid, resolved_sys)

        # Initialize site parameters from site_location
        if site_location:
            STRUCTURAL_BRIDGE._map_site_inputs(pid, {"location_name": site_location}, default_location=site_location)
        elif payload.get("auto_preset", True):
            STRUCTURAL_BRIDGE._map_site_inputs(pid, {}, default_location="Tamil Nadu")

        comp = STRUCTURAL_BRIDGE.assess_input_completeness(pid)
        return {
            "success": True,
            "project_id": pid,
            "mounting_system": resolved_sys.value,
            "project": proj,
            "input_completeness": comp,
            "message": f"Structural project '{pid}' successfully created."
        }
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail=f"Project ID '{pid}' already exists.")
    except Exception as e:
        if project_created:
            STRUCTURAL_BRIDGE.db.delete_project(pid)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail=f"Failed to create project: {e}")


@app.get("/api/structural/projects/{project_id}")
async def api_get_structural_project_details(
    project_id: str,
    x_owner_token: Optional[str] = Header(None),
):
    """Retrieves complete project details including site, module, geometry, sections, completeness, and latest run."""
    verify_structural_auth(x_owner_token=x_owner_token)
    from structural.integration import STRUCTURAL_BRIDGE
    from structural.holds import MASTER_VERIFICATION_REGISTER
    if not STRUCTURAL_BRIDGE:
        raise HTTPException(status_code=503, detail="Structural calculation subsystem unavailable.")

    proj = STRUCTURAL_BRIDGE.db.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail=f"Structural project '{project_id}' not found.")

    site = STRUCTURAL_BRIDGE.db.get_site(project_id)
    site_dict = None
    if site:
        site_dict = site.__dict__.copy()
        with STRUCTURAL_BRIDGE.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT provenance_level, provenance_source, updated_at FROM project_sites WHERE project_id = ?;", (project_id,))
            s_row = cur.fetchone()
            if s_row:
                site_dict["provenance_level"] = s_row["provenance_level"]
                site_dict["provenance_source"] = s_row["provenance_source"] or "IS 875 Reference"
                site_dict["updated_at"] = s_row["updated_at"]

        loc_u = (site.location_name or "").upper()
        if "SALEM" in loc_u:
            site_dict["is_annex_a_listed"] = False
            site_dict["code_reference"] = "IS 875 (Part 3): 2015 Figure 1 & Annex A"
            site_dict["verification_flag"] = "UNVERIFIED_COORDINATES_FLAGGED (Hold WIND_COORD_UNVERIFIED_HOLD Active)"
            site_dict["location_provenance_notes"] = "Salem is unlisted in IS 875:2015 Annex A Table. Basic wind speed 39.0 m/s is a provisional configured regional contour interpretation. Automated GIS contour interpolation is not implemented. Mandatory site coordinate & local wind speed verification hold remains enforced."
        else:
            site_dict["is_annex_a_listed"] = True
            site_dict["code_reference"] = "IS 875 (Part 3): 2015 Annex A Table"
            site_dict["verification_flag"] = "VERIFIED_PER_ANNEX_A_TABLE"
            site_dict["location_provenance_notes"] = f"Basic wind speed {site.basic_wind_speed_vb} m/s verified against IS 875:2015 Annex A Table."

    module = STRUCTURAL_BRIDGE.db.get_module(project_id)
    geom = STRUCTURAL_BRIDGE.db.get_geometry(project_id)
    comp = STRUCTURAL_BRIDGE.assess_input_completeness(project_id)
    latest_run = STRUCTURAL_BRIDGE.db.get_latest_run_for_project(project_id)
    link = STRUCTURAL_BRIDGE.db.get_link_by_project(project_id)
    active_holds = MASTER_VERIFICATION_REGISTER.get_active_holds_for_system(proj["mounting_system"])

    # Collect sections
    sections = {}
    for c in ("PURLIN", "RAFTER", "COLUMN", "RAIL", "BRACING", "STRUT"):
        sec = STRUCTURAL_BRIDGE.db.get_section(project_id, c)
        if sec:
            sections[c] = {
                "designation": sec.designation,
                "profile_type": sec.profile_type,
                "area_mm2": sec.area_mm2,
                "Ixx_mm4": sec.Ixx_mm4,
                "Iyy_mm4": sec.Iyy_mm4,
                "Zxx_mm3": sec.Zxx_mm3,
                "Zyy_mm3": sec.Zyy_mm3,
                "mass_kg_m": sec.mass_kg_m,
                "material": sec.material.grade,
                "fy_mpa": sec.material.yield_strength_mpa,
                "standard_reference": sec.material.standard_reference,
            }

    geom_dict = {
        "rows": geom.rows,
        "columns": geom.columns,
        "total_modules": geom.total_modules,
        "purlin_spacing_mm": geom.purlin_spacing_mm,
        "rafter_spacing_mm": geom.rafter_spacing_mm,
        "ground_clearance_mm": geom.ground_clearance_mm,
        "orientation": geom.orientation,
        "total_capacity_kw": geom.total_capacity_kw,
    } if geom else None

    # Enrich project object directly
    proj_dict = dict(proj)
    proj_dict["site_inputs"] = site_dict
    proj_dict["module_spec"] = module.__dict__ if module else None
    proj_dict["array_geometry"] = geom_dict
    proj_dict["sections"] = sections
    proj_dict["input_completeness"] = comp
    proj_dict["latest_run"] = latest_run

    # Phase 1.5.2 Site Coordinate, Wind & Roof Validation Audit
    site_val = STRUCTURAL_BRIDGE.audit_site_and_roof_validation(project_id)
    proj_dict["site_validation"] = site_val

    return {
        "project": proj_dict,
        "associated_quotation_no": link["quotation_no"] if link else None,
        "site": site_dict,
        "site_inputs": site_dict,
        "site_validation": site_val,
        "module": module.__dict__ if module else None,
        "module_spec": module.__dict__ if module else None,
        "geometry": geom_dict,
        "array_geometry": geom_dict,
        "sections": sections,
        "input_completeness": comp,
        "latest_run": latest_run,
        "active_holds_count": len(active_holds),
        "active_holds": [h.hold_id for h in active_holds],
        "can_approve_for_construction": False,
        "approval_status": "BLOCKED_BY_ENGINEERING_HOLDS",
        "watermark": "PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION",
    }


@app.get("/api/structural/projects/{project_id}/site-validation")
async def api_get_structural_project_site_validation(
    project_id: str,
    x_owner_token: Optional[str] = Header(None),
):
    """
    Phase 1.5.2: Audits site coordinates, IS 875 wind parameters, and host-structure
    roof inspection evidence against physical engineering criteria (WP-04, WP-05, WP-06).
    """
    verify_structural_auth(x_owner_token=x_owner_token)
    from structural.integration import STRUCTURAL_BRIDGE
    if not STRUCTURAL_BRIDGE:
        raise HTTPException(status_code=503, detail="Structural calculation subsystem unavailable.")

    proj = STRUCTURAL_BRIDGE.db.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail=f"Structural project '{project_id}' not found.")

    try:
        val = STRUCTURAL_BRIDGE.audit_site_and_roof_validation(project_id)
        return {"project_id": project_id, "validation": val}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/structural/projects/{project_id}/inputs")
async def api_update_structural_project_inputs(
    project_id: str,
    payload: Dict[str, Any] = Body(...),
    x_owner_token: Optional[str] = Header(None),
):
    """Updates structural project inputs (site, module, geometry, sections, metadata)."""
    verify_structural_auth(x_owner_token=x_owner_token)
    from structural.integration import STRUCTURAL_BRIDGE
    if not STRUCTURAL_BRIDGE:
        raise HTTPException(status_code=503, detail="Structural calculation subsystem unavailable.")

    proj = STRUCTURAL_BRIDGE.db.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail=f"Structural project '{project_id}' not found.")

    try:
        comp = STRUCTURAL_BRIDGE.update_project_inputs(project_id, payload)
        return {
            "success": True,
            "project_id": project_id,
            "input_completeness": comp,
            "message": "Project inputs updated successfully."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update project inputs: {e}")


@app.post("/api/structural/projects/{project_id}/calculate")
async def api_calculate_structural_project(
    project_id: str,
    payload: Dict[str, Any] = Body({}),
    x_owner_token: Optional[str] = Header(None),
):
    """Executes structural calculation workflow for a project."""
    verify_structural_auth(x_owner_token=x_owner_token)
    from structural.integration import STRUCTURAL_BRIDGE
    if not STRUCTURAL_BRIDGE:
        raise HTTPException(status_code=503, detail="Structural calculation subsystem unavailable.")

    proj = STRUCTURAL_BRIDGE.db.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail=f"Structural project '{project_id}' not found.")

    try:
        walkway_w = float(payload.get("walkway_width_m", 0.80))
        ballast_w = float(payload.get("ballast_weight_kn_per_m2", 0.75))
        friction_mu = float(payload.get("friction_coeff_mu", 0.40))
        clamp_cap = float(payload.get("clamp_capacity_kn", 3.50))
        bracket_sp = float(payload.get("bracket_spacing_mm", 1400.0))
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid numerical calculation input: {e}")

    for k, v in [
        ("walkway_width_m", walkway_w),
        ("ballast_weight_kn_per_m2", ballast_w),
        ("friction_coeff_mu", friction_mu),
        ("clamp_capacity_kn", clamp_cap),
        ("bracket_spacing_mm", bracket_sp),
    ]:
        if math.isnan(v) or math.isinf(v):
            raise HTTPException(status_code=400, detail=f"Parameter '{k}' must be a finite numerical value.")

    if walkway_w <= 0 or ballast_w <= 0 or clamp_cap <= 0 or bracket_sp <= 0:
        raise HTTPException(status_code=400, detail="Physical dimensions and capacities must be strictly positive.")

    if not (0.0 < friction_mu <= 1.0):
        raise HTTPException(status_code=400, detail="Friction coefficient mu must be in physical range (0.0, 1.0].")

    try:
        result = STRUCTURAL_BRIDGE.execute_project_assessment(
            project_id=project_id,
            walkway_width_m=walkway_w,
            ballast_weight_kn_per_m2=ballast_w,
            friction_coeff_mu=friction_mu,
            clamp_capacity_kn=clamp_cap,
            bracket_spacing_mm=bracket_sp,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Structural calculation failed: {e}")


@app.get("/api/structural/runs")
async def api_list_all_structural_runs(
    x_owner_token: Optional[str] = Header(None),
):
    """Retrieves all historical calculation runs across all projects."""
    verify_structural_auth(x_owner_token=x_owner_token)
    from structural.integration import STRUCTURAL_BRIDGE
    if not STRUCTURAL_BRIDGE:
        raise HTTPException(status_code=503, detail="Structural calculation subsystem unavailable.")

    runs = STRUCTURAL_BRIDGE.db.list_calculation_runs(None)
    return {"runs": runs, "total": len(runs)}


@app.get("/api/structural/projects/{project_id}/runs")
async def api_list_structural_project_runs(
    project_id: str,
    x_owner_token: Optional[str] = Header(None),
):
    """Retrieves all historical calculation runs for a project."""
    verify_structural_auth(x_owner_token=x_owner_token)
    from structural.integration import STRUCTURAL_BRIDGE
    if not STRUCTURAL_BRIDGE:
        raise HTTPException(status_code=503, detail="Structural calculation subsystem unavailable.")

    proj = STRUCTURAL_BRIDGE.db.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail=f"Structural project '{project_id}' not found.")

    runs = STRUCTURAL_BRIDGE.db.list_calculation_runs(project_id)
    return {"project_id": project_id, "runs": runs, "total": len(runs)}


@app.get("/api/structural/runs/{run_id}")
async def api_get_structural_run_details(
    run_id: str,
    x_owner_token: Optional[str] = Header(None),
):
    """Retrieves full details for a specific historical calculation run, including immutable input snapshot."""
    verify_structural_auth(x_owner_token=x_owner_token)
    from structural.integration import STRUCTURAL_BRIDGE
    if not STRUCTURAL_BRIDGE:
        raise HTTPException(status_code=503, detail="Structural calculation subsystem unavailable.")

    run = STRUCTURAL_BRIDGE.db.get_calculation_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Calculation run '{run_id}' not found.")

    reproducible, rep_msg = STRUCTURAL_BRIDGE.db.verify_reproducibility(run_id)
    return {
        "run": run,
        "reproducibility": {
            "verified": reproducible,
            "message": rep_msg,
        },
        "watermark": "PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION",
        "approval_status": "BLOCKED_BY_ENGINEERING_HOLDS",
    }


@app.get("/api/structural/holds")
async def api_get_structural_holds(
    system: Optional[str] = Query(None, description="Filter holds by mounting system A, B, C, D"),
    x_owner_token: Optional[str] = Header(None),
):
    """Lists all 12 canonical engineering verification holds and overall governance status."""
    verify_structural_auth(x_owner_token=x_owner_token)
    from structural.holds import MASTER_VERIFICATION_REGISTER
    all_holds = MASTER_VERIFICATION_REGISTER.get_all_holds()

    holds_data = []
    for h in all_holds:
        d = h.to_dict()
        d["applies_to_a"] = h.applies_to("System A")
        d["applies_to_b"] = h.applies_to("System B")
        d["applies_to_c"] = h.applies_to("System C")
        d["applies_to_d"] = h.applies_to("System D")

        if system:
            s_key = system.strip().upper()
            sys_name = f"System {s_key}"
            if not h.applies_to(sys_name):
                continue
        holds_data.append(d)

    return {
        "governance_status": "ENGINEERING VERIFICATION PENDING",
        "active_holds_count": len(holds_data),
        "total_canonical_holds": 12,
        "afc_status": "STRICTLY BLOCKED",
        "holds": holds_data,
        "watermark": "PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION",
        "disclaimer": "PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION. Manual hold release is disabled in Phase 1.4 per TNCDBR-2019 statutory mandates.",
    }


@app.get("/api/structural/projects/{project_id}/deliverables/{item}")
async def api_download_structural_deliverable(
    project_id: str,
    item: str,
    require_approved: bool = Query(False, description="Request approved for construction deliverable (blocked while holds active)"),
    x_owner_token: Optional[str] = Header(None),
):
    """One-click download endpoint for structural assessment deliverables."""
    verify_structural_auth(x_owner_token=x_owner_token)
    from structural.integration import STRUCTURAL_BRIDGE
    from structural.holds import MASTER_VERIFICATION_REGISTER
    if not STRUCTURAL_BRIDGE:
        raise HTTPException(status_code=503, detail="Structural calculation subsystem unavailable.")

    proj = STRUCTURAL_BRIDGE.db.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail=f"Structural project '{project_id}' not found.")

    clean_id = re.sub(r'[^A-Za-z0-9]', '_', project_id)

    # 1. Report deliverable
    if item == "report":
        try:
            report_md = STRUCTURAL_BRIDGE.generate_structural_assessment_report(project_id)
            return StreamingResponse(
                io.BytesIO(report_md.encode("utf-8")),
                media_type="text/markdown",
                headers={"Content-Disposition": f"attachment; filename=Structural_Assessment_{clean_id}.md"}
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    # 2. DXF CAD deliverable
    elif item == "dxf":
        if require_approved and not MASTER_VERIFICATION_REGISTER.can_label_approved_for_construction(proj["mounting_system"]):
            active_holds = MASTER_VERIFICATION_REGISTER.get_active_holds_for_system(proj["mounting_system"])
            raise HTTPException(
                status_code=403,
                detail=f"Approved for Construction (AFC) drawing export is strictly forbidden: {len(active_holds)} active hold(s) enforced."
            )
        out_dir = getattr(STRUCTURAL_BRIDGE, "drawing_output_dir", None) or os.path.join(BASE_DIR, "generated_drawings")
        os.makedirs(out_dir, exist_ok=True)
        dxf_path = os.path.join(out_dir, f"Structural_Layout_{clean_id}.dxf")
        try:
            dxf_file = STRUCTURAL_BRIDGE.generate_structural_dxf(
                project_id,
                output_path=dxf_path,
                require_approved=require_approved
            )
            return FileResponse(
                dxf_file,
                media_type="application/dxf",
                filename=f"Structural_Layout_{clean_id}.dxf"
            )
        except PermissionError as pe:
            raise HTTPException(status_code=403, detail=str(pe))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"DXF generation failed: {e}")

    # 3. Calculation Summary
    elif item == "summary":
        summary = STRUCTURAL_BRIDGE.generate_calculation_summary(project_id)
        return StreamingResponse(
            io.BytesIO(summary["summary_text"].encode("utf-8")),
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=Calculation_Summary_{clean_id}.md"}
        )

    # 4. Input Schedule
    elif item == "inputs":
        sched = STRUCTURAL_BRIDGE.generate_input_schedule(project_id)
        return StreamingResponse(
            io.BytesIO(sched["schedule_text"].encode("utf-8")),
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=Input_Schedule_{clean_id}.md"}
        )

    # 5. Section Schedule
    elif item == "sections":
        sec_sched = STRUCTURAL_BRIDGE.generate_section_schedule(project_id)
        return StreamingResponse(
            io.BytesIO(sec_sched["schedule_text"].encode("utf-8")),
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=Section_Schedule_{clean_id}.md"}
        )

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid deliverable item '{item}'. Supported: report, dxf, summary, inputs, sections."
        )


@app.put("/api/quotations/{quotation_no:path}/status")
async def api_update_quotation_status(quotation_no: str, payload: Dict[str, Any] = Body(...)):
    """Updates quotation status (e.g. Draft -> Presented -> Accepted)."""
    st = payload.get("status")
    if not st:
        raise HTTPException(status_code=400, detail="Missing status field.")

    # Strictly block unauthorized AFC approval attempts
    if str(st).strip().upper() in ["APPROVED_FOR_CONSTRUCTION", "AFC", "CONSTRUCTION_APPROVED", "APPROVED"]:
        raise HTTPException(
            status_code=403,
            detail="Approved for Construction (AFC) status is strictly forbidden while active engineering verification holds remain enforced."
        )

    try:
        update_status(quotation_no, st)
        return {"success": True, "message": f"Quotation {quotation_no} updated to {st}."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/quotations/{quotation_no:path}")
async def api_get_quotation_details(quotation_no: str):
    """Retrieves full saved quotation JSON details to reopen in the editor."""
    data = get_quotation(quotation_no)
    if not data:
        raise HTTPException(status_code=404, detail=f"Quotation {quotation_no} not found.")
    versions = get_quotation_versions(quotation_no)
    return {"quotation": data, "versions": versions}


if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 70)
    print("🚀 Launching TNEB Extractor Web UI on http://127.0.0.1:8090")
    print("=" * 70 + "\n")
    uvicorn.run("server:app", host="127.0.0.1", port=8090, reload=False)
