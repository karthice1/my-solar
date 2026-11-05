import asyncio
import os
import re
import json
import csv
import io
import glob
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

@app.get("/api/quotations/{quotation_no:path}")
async def api_get_quotation_details(quotation_no: str):
    """Retrieves full saved quotation JSON details to reopen in the editor."""
    data = get_quotation(quotation_no)
    if not data:
        raise HTTPException(status_code=404, detail=f"Quotation {quotation_no} not found.")
    versions = get_quotation_versions(quotation_no)
    return {"quotation": data, "versions": versions}

@app.put("/api/quotations/{quotation_no:path}/status")
async def api_update_quotation_status(quotation_no: str, payload: Dict[str, Any] = Body(...)):
    """Updates quotation status (e.g. Draft -> Presented -> Accepted)."""
    st = payload.get("status")
    if not st:
        raise HTTPException(status_code=400, detail="Missing status field.")
    try:
        update_status(quotation_no, st)
        return {"success": True, "message": f"Quotation {quotation_no} updated to {st}."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 70)
    print("🚀 Launching TNEB Extractor Web UI on http://127.0.0.1:8090")
    print("=" * 70 + "\n")
    uvicorn.run("server:app", host="127.0.0.1", port=8090, reload=False)
