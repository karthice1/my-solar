#!/usr/bin/env python3
"""
TNEB Account Automation & Extraction Tool
1. Logs into https://www.tnebnet.org/awp/login?locale=ta (Tamil/English portal)
2. Auto-solves 5-digit image captcha with multi-threshold OCR
3. Enters user-provided TNEB credentials (User ID and Password)
4. Navigates to 'Add Number' (/awp/consumerGroup?create=true)
5. Inputs consumer number, checks details, and confirms addition
6. Navigates to 'Account Summary' (/awp/billStatus)
7. Locates consumer connection and loads detconws.php detailed billing ledger
8. Extracts all parameters (consumer info, connection specs, dues, past 24 billing cycles)
9. Sizing Solar Panel Capacity (Past 6 Cycles Units ÷ 1500 = Solar kW)
10. Auto-deletes consumer number from TNEB account
11. Generates comprehensive report in Terminal, Markdown, and JSON
"""

import sys
import os
import io
import re
import json
import math
import asyncio
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from playwright.async_api import async_playwright

BASE_URL = "https://www.tnebnet.org"
LOGIN_URL = "https://www.tnebnet.org/awp/login?locale=ta"

def solve_ocr_captcha(png_bytes: bytes) -> str:
    """Solves TNEB 5-digit captcha using contrast stretching and multi-thresholding."""
    img = Image.open(io.BytesIO(png_bytes)).convert('L')
    img = img.resize((img.width * 3, img.height * 3), Image.Resampling.LANCZOS)
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.5)
    
    for thresh in [110, 125, 140, 155, 95, 80]:
        bw = img.point(lambda p: 255 if p > thresh else 0)
        bw_smooth = bw.filter(ImageFilter.MedianFilter(size=3))
        for psm in [7, 8, 6]:
            txt = pytesseract.image_to_string(bw_smooth, config=f'--psm {psm} -c tessedit_char_whitelist=0123456789').strip()
            digits = re.sub(r'[^0-9]', '', txt)
            if len(digits) == 5:
                return digits
    return None

async def solve_captcha_with_retries(page, max_retries=6) -> str:
    for attempt in range(max_retries):
        cap_el = page.locator('#CaptchaImgID')
        await cap_el.wait_for(state="visible", timeout=10000)
        cap_png = await cap_el.screenshot()
        code = solve_ocr_captcha(cap_png)
        if code:
            print(f"   [Captcha] Solved 5-digit code: '{code}' (Attempt {attempt + 1})")
            return code
            
        print(f"   [Captcha] Attempt {attempt + 1} failed, reloading captcha...")
        try:
            rel = page.locator("a:has-text('Reload')")
            if await rel.count() > 0:
                await rel.first.click()
                await asyncio.sleep(1.5)
            else:
                await page.reload()
                await asyncio.sleep(2)
        except Exception:
            await page.reload()
            await asyncio.sleep(2)
    return None

async def login_tneb(page, user_id: str, password: str, max_login_retries: int = 5) -> bool:
    print(f"1. Navigating to TNEB Portal ({LOGIN_URL})...")
    for attempt in range(max_login_retries):
        await page.goto(LOGIN_URL, timeout=35000)
        await asyncio.sleep(2)
        
        captcha_code = await solve_captcha_with_retries(page)
        if not captcha_code:
            print("   [Error] Could not solve captcha, retrying page...")
            continue
            
        print(f"2. Entering credentials for User: '{user_id}' (Login Attempt {attempt + 1}/{max_login_retries})...")
        await page.fill('#userName', user_id)
        await page.fill('#password', password)
        await page.fill('#CaptchaID', captcha_code)
        
        await page.click('input[name="submit"]')
        await asyncio.sleep(4)
        
        # Check for error elements or login failure
        err_loc = page.locator(".error, .ui-messages-error, .ui-messages-error-summary, .ui-messages-error-detail, #form\\:msg")
        if "login_error" in page.url or await err_loc.count() > 0:
            err_text = ""
            try:
                if await err_loc.count() > 0:
                    err_text = " ".join([await e.inner_text() for e in await err_loc.all()]).strip()
            except Exception:
                pass
            
            # Check for credential error vs captcha error
            if any(k in err_text.lower() for k in ["invalid user", "password", "user id", "கடவுச்சொல்", "பயனர்பெயர்"]):
                print(f"   [Error] Authentication rejected by TNEB portal: {err_text or 'Invalid User ID or Password'}")
                return False
                
            print(f"   [Notice] Captcha incorrect on attempt {attempt + 1} ({err_text or 'Retrying...'}), retrying with fresh captcha...")
            await asyncio.sleep(1)
            continue
            
        print(f"3. Login successful! Current URL: {page.url}")
        return True
        
    print("   [Error] Failed to login after multiple attempts.")
    return False

def init_connection_state(consumer_no: str) -> Dict[str, Any]:
    """Initializes the connection lifecycle and protection state tracking."""
    norm_no = normalize_consumer_number(consumer_no)
    return {
        "requested_consumer_number": norm_no,
        "raw_requested_consumer_number": str(consumer_no or "").strip(),
        "was_registered_before_extraction": False,
        "is_primary_connection": False,
        "is_secondary_connection": False,
        "added_by_current_extraction": False,
        "extraction_completed": False,
        "cleanup_attempted": False,
        "cleanup_completed": False,
        "cleanup_status": "NOT_REQUIRED",
        "cleanup_message": ""
    }

async def scan_registered_connections(page) -> Dict[str, Dict[str, Any]]:
    """
    Audits the TNEB registered connections list (/awp/consumerGroup?delete=true)
    before any extraction actions take place.
    Determines primary status using reliable portal evidence:
    Connections with NO delete button are primary accounts (protected by TNEB portal design).
    Connections WITH a delete button are secondary accounts.
    """
    registered = {}
    try:
        print(f"\n[Audit] Inspecting existing registered connections on portal account...")
        await page.goto(f"{BASE_URL}/awp/consumerGroup?delete=true", timeout=25000)
        await asyncio.sleep(2)
        
        paginator_pages = page.locator(".ui-paginator-top .ui-paginator-page")
        num_pages = max(1, await paginator_pages.count())
        
        for page_idx in range(num_pages):
            if num_pages > 1:
                p_btn = page.locator(f".ui-paginator-top .ui-paginator-page:has-text('{page_idx + 1}')")
                if await p_btn.count() > 0:
                    await p_btn.first.click()
                    await asyncio.sleep(1.5)
                    
            rows_info = await page.evaluate("""() => {
                const trs = Array.from(document.querySelectorAll('tbody[id*="j_idt115_data"] tr'));
                return trs.map((tr) => {
                    const tds = Array.from(tr.querySelectorAll('td')).map(td => td.innerText.trim());
                    const btn = tr.querySelector('button[title*="நீக்க"], button.ui-button-icon-only');
                    return {
                        consumerNo: tds.length > 0 ? tds[0] : '',
                        consumerName: tds.length > 1 ? tds[1] : '',
                        hasButton: !!btn
                    };
                });
            }""")
            
            for r in rows_info:
                norm = normalize_consumer_number(r.get("consumerNo", ""))
                if norm:
                    has_btn = bool(r.get("hasButton", False))
                    registered[norm] = {
                        "consumer_no": norm,
                        "raw_consumer_no": r.get("consumerNo", ""),
                        "consumer_name": r.get("consumerName", ""),
                        "is_primary": not has_btn,
                        "has_delete_btn": has_btn
                    }
        print(f"   [Audit] {len(registered)} pre-existing connection(s) identified on account.")
        for cno, cinfo in registered.items():
            kind = "PRIMARY (Protected)" if cinfo["is_primary"] else "SECONDARY (Pre-existing)"
            print(f"    • Consumer {cno}: {cinfo['consumer_name']} [{kind}]")
    except Exception as e:
        print(f"   [Audit Notice] Could not complete pre-audit: {e}")
        
    return registered

async def add_consumer_number(page, consumer_no: str) -> Dict[str, Any]:
    clean_no = normalize_consumer_number(consumer_no)
    print(f"\n4. Navigating to 'Add Number' page (/awp/consumerGroup?create=true)...")
    await page.goto(f"{BASE_URL}/awp/consumerGroup?create=true", timeout=25000)
    await asyncio.sleep(2)
    
    # Check if consumer input exists
    ref_input = page.locator('input[id*="consumerRef"]')
    await ref_input.wait_for(state="visible", timeout=10000)
    
    print(f"5. Entering Consumer Number: '{clean_no}'...")
    await ref_input.fill(clean_no)
    
    # Click 'விவரம் சோதிக்க' (Verify details)
    verify_btn = page.locator('button[type="submit"]:has-text("விவரம் சோதிக்க"), button[type="submit"]:has-text("Check"), button[id*="j_idt123"]')
    await verify_btn.click()
    await asyncio.sleep(3)
    
    page_text = await page.inner_text('body')
    
    # Extract preview verification details
    name_m = re.search(r'நுகர்வோர்\s*பெயர்\s*[:\s]*([^\n\r]+)', page_text) or re.search(r'Consumer\s*Name\s*[:\s]*([^\n\r]+)', page_text)
    addr_m = re.search(r'முகவரி\s*[:\s]*([^\n\r]+)', page_text) or re.search(r'Address\s*[:\s]*([^\n\r]+)', page_text)
    status_m = re.search(r'மின்\s*இணைப்பு\s*நிலை\s*[:\s]*([^\n\r]+)', page_text) or re.search(r'Status\s*[:\s]*([^\n\r]+)', page_text)
    
    verified_name = name_m.group(1).strip() if name_m else "Not Displayed"
    verified_addr = addr_m.group(1).strip() if addr_m else "Not Displayed"
    verified_status = status_m.group(1).strip() if status_m else "Live"
    
    print(f"   [Verified Connection] Name: {verified_name}")
    print(f"   [Verified Connection] Address: {verified_addr}")
    print(f"   [Verified Connection] Status: {verified_status}")
    
    # Click 'உறுதி செய்க' (Confirm)
    confirm_btn = page.locator('button:has-text("உறுதி செய்க"), button:has-text("Confirm"), button[id*="j_idt132"]')
    was_added = False
    if await confirm_btn.count() > 0 and await confirm_btn.is_visible():
        print("6. Clicking 'உறுதி செய்க' (Confirm) button to add connection...")
        try:
            await confirm_btn.click()
            await asyncio.sleep(3)
            print("   Connection confirmed successfully!")
            was_added = True
        except Exception as e:
            print(f"   Note on confirmation: {e}")
            was_added = False
    else:
        print("   Connection already confirmed/registered on this account.")
        was_added = False
        
    return {
        "consumer_no": clean_no,
        "name": verified_name,
        "address": verified_addr,
        "status": verified_status,
        "was_added": was_added
    }

def normalize_consumer_number(val: Any) -> str:
    """
    Normalizes a TNEB consumer number by removing permitted formatting characters
    (whitespace, hyphens, slashes, underscores) and returning clean digits.
    Handles empty, None, or malformed input safely.
    """
    if val is None:
        return ""
    s = str(val).strip()
    if not s:
        return ""
    cleaned = re.sub(r'[\s\-_/]', '', s)
    return re.sub(r'[^0-9]', '', cleaned)

def is_exact_consumer_match(target_no: Any, candidate_no: Any) -> bool:
    """
    Performs strict exact equality matching between target and candidate consumer numbers.
    Rejects partial matches, prefix matches, suffix matches, and empty/invalid values.
    """
    norm_target = normalize_consumer_number(target_no)
    norm_candidate = normalize_consumer_number(candidate_no)
    
    if not norm_target or not norm_candidate:
        return False
        
    return norm_target == norm_candidate

def find_matching_consumer_connection(page_rows: List[Dict[str, Any]], target_consumer_no: str) -> Optional[Dict[str, Any]]:
    """
    Searches a list of table rows from Account Summary for an exact matching consumer connection.
    Returns the row dict if found, or None if no exact match exists.
    Never defaults to first connection.
    """
    norm_target = normalize_consumer_number(target_consumer_no)
    if not norm_target:
        return None
        
    for r in page_rows:
        candidate = r.get("consumerNo", "")
        if is_exact_consumer_match(norm_target, candidate):
            return r
    return None

def extract_ledger_consumer_number(html: str, text: str) -> str:
    """
    Retrieves and normalizes the consumer number displayed on the detailed ledger page (detconws.php).
    Searches for CONSUMER NUMBER in the header table.
    """
    # 1. Search in raw HTML for CONSUMER NUMBER pattern
    m = re.search(r'CONSUMER\s*NUMBER\s*[:\-]?\s*(?:&nbsp;|\s)*([0-9\s\-_/]+)', html, re.IGNORECASE)
    if m:
        num = normalize_consumer_number(m.group(1))
        if num:
            return num
            
    # 2. Search in text representation
    m_txt = re.search(r'CONSUMER\s*NUMBER\s*[:\-]?\s*([0-9\s\-_/]+)', text, re.IGNORECASE)
    if m_txt:
        num = normalize_consumer_number(m_txt.group(1))
        if num:
            return num
            
    # 3. Table cell search
    trs = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL | re.IGNORECASE)
    for tr in trs:
        if 'CONSUMER' in tr.upper() and 'NUMBER' in tr.upper():
            tds = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, re.DOTALL | re.IGNORECASE)
            for td in tds:
                clean_td = re.sub(r'<[^>]+>', ' ', td).replace('&nbsp;', ' ').strip()
                m_td = re.search(r'CONSUMER\s*NUMBER\s*[:\-]?\s*([0-9\s\-_/]+)', clean_td, re.IGNORECASE)
                if m_td:
                    num = normalize_consumer_number(m_td.group(1))
                    if num:
                        return num
    return ""

async def extract_account_summary_and_details(context, page, target_consumer_no: str, conn_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    clean_target = normalize_consumer_number(target_consumer_no)
    if not clean_target:
        print(f"   [Error] Empty or invalid consumer number requested: '{target_consumer_no}'")
        return {
            "error": "The consumer number you entered could not be found in your TNEB account. Please verify the consumer number and try again. No billing information has been extracted.",
            "title": "Consumer Number Not Found",
            "consumer_no": target_consumer_no or ""
        }

    print(f"\n7. Navigating to 'Account Summary' (/awp/billStatus)...")
    await page.goto(f"{BASE_URL}/awp/billStatus", timeout=25000)
    await asyncio.sleep(3)
    
    # Check pagination pages if any
    paginator_pages = page.locator(".ui-paginator-top .ui-paginator-page")
    num_pages = max(1, await paginator_pages.count())
    print(f"8. Scanning Account Summary ({num_pages} page(s) available)...")
    
    target_btn = None
    matched_no = ""
    matched_name = ""
    
    for page_idx in range(num_pages):
        if num_pages > 1:
            p_btn = page.locator(f".ui-paginator-top .ui-paginator-page:has-text('{page_idx + 1}')")
            if await p_btn.count() > 0:
                await p_btn.first.click()
                await asyncio.sleep(2)
                
        page_forms = await page.evaluate("""() => {
            const forms = Array.from(document.querySelectorAll('form[action*=\"detconws.php\"]'));
            return forms.map((f, idx) => {
                const tr = f.closest('tr');
                const tds = tr ? Array.from(tr.querySelectorAll('td')).map(td => td.innerText.trim()) : [];
                return {
                    index: idx,
                    consumerNo: tds.length > 0 ? tds[0] : '',
                    consumerName: tds.length > 1 ? tds[1] : '',
                    address: tds.length > 2 ? tds[2] : ''
                };
            });
        }""")
        
        matched_row = find_matching_consumer_connection(page_forms, clean_target)
        if matched_row:
            target_btn = page.locator("form[action*='detconws.php'] input[type='submit']").nth(matched_row['index'])
            matched_no = matched_row.get('consumerNo', '')
            matched_name = matched_row.get('consumerName', '')
            print(f"   -> Exact Match Found on Page {page_idx + 1}, Row #{matched_row['index'] + 1}: {matched_no} ({matched_name})")
            if conn_info and not conn_info.get("name"):
                conn_info["name"] = matched_name
            break
            
    # Strict failure handling: If no exact match found, NEVER default to first connection!
    if not target_btn:
        print(f"   [Error] Consumer '{clean_target}' not found in Account Summary table.")
        return {
            "error": "The consumer number you entered could not be found in your TNEB account. Please verify the consumer number and try again. No billing information has been extracted.",
            "title": "Consumer Number Not Found",
            "consumer_no": clean_target
        }
        
    print(f"9. Opening detailed ledger (detconws.php) for Consumer '{clean_target}'...")
    async with context.expect_page(timeout=25000) as new_page_info:
        await target_btn.click()
        
    det_page = await new_page_info.value
    await det_page.wait_for_load_state("networkidle", timeout=25000)
    await asyncio.sleep(2)
    
    det_html = await det_page.content()
    det_text = await det_page.inner_text('body')
    
    # Verification Step on the Ledger Page:
    ledger_consumer_no = extract_ledger_consumer_number(det_html, det_text)
    if not is_exact_consumer_match(clean_target, ledger_consumer_no):
        await det_page.close()
        print(f"   [Error] Consumer verification failed! Requested '{clean_target}', but ledger showed '{ledger_consumer_no}'.")
        return {
            "error": "Consumer verification failed. The account details retrieved from TNEB do not match the requested consumer number. Extraction has been stopped for your protection.",
            "title": "Consumer Verification Failed",
            "consumer_no": clean_target,
            "ledger_consumer_no": ledger_consumer_no
        }
        
    print(f"   ✓ Ledger verification confirmed: Consumer Number matches exact requested '{clean_target}'.")
    
    # Save snapshot and html for audit trail only after verification passes
    out_dir = "/Users/karthik/tneb-account-extractor"
    os.makedirs(out_dir, exist_ok=True)
    screenshot_path = os.path.join(out_dir, f"tneb_detail_{clean_target}.png")
    html_path = os.path.join(out_dir, f"tneb_detail_{clean_target}.html")
    await det_page.screenshot(path=screenshot_path, full_page=True)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(det_html)
    print(f"   Full ledger screenshot saved to: {screenshot_path}")
    print(f"   Raw HTML saved to: {html_path}")
    
    # Parse detailed data
    extracted = parse_detconws_page(det_html, det_text, default_conn_info=conn_info)
    if not extracted.get("consumer_no"):
        extracted["consumer_no"] = clean_target
    await det_page.close()
    
    return extracted

async def safe_cleanup_consumer_number(page, connection_state: Dict[str, Any], user_id: str = "") -> Dict[str, Any]:
    """
    Safely executes consumer cleanup according to strict protection rules:
    - Rule A: NEVER delete primary consumer connection.
    - Rule B: NEVER delete pre-existing secondary consumer connections.
    - Rule E: NEVER delete if connection identity or origin is ambiguous.
    - Rule C & D: ONLY delete temporary connections created by the current extraction run.
    - Performs exact matching on the portal's deletion table.
    - Performs independent post-deletion verification by re-auditing the registered list.
    """
    target_no = connection_state.get("requested_consumer_number", "")
    if not target_no:
        connection_state["cleanup_status"] = "SAFETY_PREVENTED"
        connection_state["cleanup_message"] = "Automatic deletion was prevented because the connection's original registration status could not be verified. No deletion was attempted."
        return connection_state

    # Rule A: Primary consumer connection
    if connection_state.get("is_primary_connection"):
        connection_state["cleanup_attempted"] = False
        connection_state["cleanup_completed"] = False
        connection_state["cleanup_status"] = "RETAINED_PRIMARY"
        connection_state["cleanup_message"] = "Primary consumer connection detected. Your original TNEB connection has been retained."
        print(f"\n[Cleanup Protection] {connection_state['cleanup_message']}")
        return connection_state

    # Rule B: Secondary connection already registered before extraction
    if connection_state.get("was_registered_before_extraction"):
        connection_state["cleanup_attempted"] = False
        connection_state["cleanup_completed"] = False
        connection_state["cleanup_status"] = "RETAINED_PREEXISTING"
        connection_state["cleanup_message"] = "This consumer connection was already registered before extraction. It has been retained."
        print(f"\n[Cleanup Protection] {connection_state['cleanup_message']}")
        return connection_state

    # Rule E: Connection was NOT added by current extraction run or identity is ambiguous
    if not connection_state.get("added_by_current_extraction"):
        connection_state["cleanup_attempted"] = False
        connection_state["cleanup_completed"] = False
        connection_state["cleanup_status"] = "SAFETY_PREVENTED"
        connection_state["cleanup_message"] = "Automatic deletion was prevented because the connection's original registration status could not be verified. No deletion was attempted."
        print(f"\n[Cleanup Protection] {connection_state['cleanup_message']}")
        return connection_state

    # Rule C & D: Temporary secondary connection added by current extraction run
    connection_state["cleanup_attempted"] = True
    print(f"\n10. Initiating verified safe cleanup for temporary connection '{target_no}'...")
    try:
        await page.goto(f"{BASE_URL}/awp/consumerGroup?delete=true", timeout=25000)
        await asyncio.sleep(2)
    except Exception as e:
        print(f"   [Cleanup Safety] Failed to navigate to delete page: {e}")
        connection_state["cleanup_completed"] = False
        connection_state["cleanup_status"] = "SAFETY_PREVENTED"
        connection_state["cleanup_message"] = "Automatic deletion was prevented because the connection's original registration status could not be verified. No deletion was attempted."
        return connection_state
    
    paginator_pages = page.locator(".ui-paginator-top .ui-paginator-page")
    num_pages = max(1, await paginator_pages.count())
    print(f"   Scanning Delete Number list ({num_pages} page(s) available)...")
    
    target_btn = None
    target_row_info = None
    table_found_anywhere = False
    
    for page_idx in range(num_pages):
        if num_pages > 1:
            p_btn = page.locator(f".ui-paginator-top .ui-paginator-page:has-text('{page_idx + 1}')")
            if await p_btn.count() > 0:
                await p_btn.first.click()
                await asyncio.sleep(1.5)
                
        page_eval = await page.evaluate("""() => {
            const tableBody = document.querySelector('tbody[id*="j_idt115_data"]');
            const form = document.querySelector('form[action*="consumerGroup"]');
            if (!tableBody && !form) {
                return { available: false, rows: [] };
            }
            const trs = Array.from(document.querySelectorAll('tbody[id*="j_idt115_data"] tr'));
            const rows = trs.map((tr, idx) => {
                const tds = Array.from(tr.querySelectorAll('td')).map(td => td.innerText.trim());
                const btn = tr.querySelector('button[title*="நீக்க"], button.ui-button-icon-only');
                return {
                    index: idx,
                    consumerNo: tds.length > 0 ? tds[0] : '',
                    consumerName: tds.length > 1 ? tds[1] : '',
                    hasButton: !!btn,
                    buttonId: btn ? btn.id : ''
                };
            });
            return { available: true, rows: rows };
        }""")
        
        if not page_eval.get("available"):
            continue
            
        table_found_anywhere = True
        rows_info = page_eval.get("rows", [])
        
        for r in rows_info:
            candidate_no = r.get("consumerNo", "")
            if is_exact_consumer_match(target_no, candidate_no):
                target_row_info = r
                if r.get("hasButton") and r.get("buttonId"):
                    target_btn = page.locator(f"[id='{r['buttonId']}']")
                break
        if target_row_info:
            break
            
    # Check if deletion form was available at all
    if not table_found_anywhere:
        print(f"   [Cleanup Safety] No deletion form or table available on portal. Stopping cleanup safely.")
        connection_state["cleanup_completed"] = False
        connection_state["cleanup_status"] = "SAFETY_PREVENTED"
        connection_state["cleanup_message"] = "Automatic deletion was prevented because the connection's original registration status could not be verified. No deletion was attempted."
        return connection_state
            
    if not target_row_info:
        # Deletion table was scanned, but target consumer number is no longer present
        connection_state["cleanup_completed"] = True
        connection_state["cleanup_status"] = "SUCCESS_REMOVED"
        connection_state["cleanup_message"] = "Temporary consumer connection successfully removed after extraction."
        print(f"   ✓ {connection_state['cleanup_message']}")
        return connection_state

    # Verification: Confirm that the portal row corresponds to the exact consumer number (target mismatch check)
    if not is_exact_consumer_match(target_no, target_row_info.get("consumerNo", "")):
        print(f"   [Cleanup Safety] Deletion target mismatch: target '{target_no}' does not match row '{target_row_info.get('consumerNo')}'. Deletion aborted.")
        connection_state["cleanup_completed"] = False
        connection_state["cleanup_status"] = "SAFETY_PREVENTED"
        connection_state["cleanup_message"] = "Automatic deletion was prevented because the connection's original registration status could not be verified. No deletion was attempted."
        return connection_state

    # Additional safety guard: If matched row has no button, it is a primary account!
    if not target_row_info.get("hasButton") or not target_btn:
        connection_state["is_primary_connection"] = True
        connection_state["cleanup_completed"] = False
        connection_state["cleanup_status"] = "RETAINED_PRIMARY"
        connection_state["cleanup_message"] = "Primary consumer connection detected. Your original TNEB connection has been retained."
        print(f"   [Cleanup Safety] {connection_state['cleanup_message']}")
        return connection_state

    # Proceed to click delete for verified temporary secondary connection
    print(f"   Clicking delete button for verified temporary connection '{target_no}'...")
    try:
        await target_btn.click()
    except Exception:
        btn_id = target_row_info.get("buttonId", "")
        await page.evaluate(f"() => {{ const el = document.getElementById('{btn_id}'); if (el) el.click(); }}")
    await asyncio.sleep(3)
    
    # Wait if ajaxloadingbar is visible
    loading = page.locator("#form\\:j_idt130, .ui-dialog:has-text('நிலை')")
    if await loading.count() > 0 and await loading.first.is_visible():
        await asyncio.sleep(2)
        
    # POST-DELETION INDEPENDENT VERIFICATION
    # Re-scan the delete number table across all pages to guarantee target_no is gone
    print(f"   Performing post-deletion audit to independently verify removal...")
    still_present = False
    verification_attempted = False
    try:
        await page.goto(f"{BASE_URL}/awp/consumerGroup?delete=true", timeout=25000)
        await asyncio.sleep(2)
        
        paginator_pages_post = page.locator(".ui-paginator-top .ui-paginator-page")
        num_pages_post = max(1, await paginator_pages_post.count())
        
        for p_idx in range(num_pages_post):
            if num_pages_post > 1:
                p_btn = page.locator(f".ui-paginator-top .ui-paginator-page:has-text('{p_idx + 1}')")
                if await p_btn.count() > 0:
                    await p_btn.first.click()
                    await asyncio.sleep(1.5)
            post_rows = await page.evaluate("""() => {
                const trs = Array.from(document.querySelectorAll('tbody[id*="j_idt115_data"] tr'));
                return trs.map(tr => {
                    const tds = Array.from(tr.querySelectorAll('td')).map(td => td.innerText.trim());
                    return tds.length > 0 ? tds[0] : '';
                });
            }""")
            for cand in post_rows:
                if is_exact_consumer_match(target_no, cand):
                    still_present = True
                    break
            if still_present:
                break
        verification_attempted = True
    except Exception as e:
        print(f"   [Cleanup Warning] Could not execute post-deletion audit: {e}")
        still_present = True
        verification_attempted = False
            
    if verification_attempted and not still_present:
        connection_state["cleanup_completed"] = True
        connection_state["cleanup_status"] = "SUCCESS_REMOVED"
        connection_state["cleanup_message"] = "Temporary consumer connection successfully removed after extraction."
        print(f"   ✓ {connection_state['cleanup_message']}")
    else:
        connection_state["cleanup_completed"] = False
        connection_state["cleanup_status"] = "FAILED_VERIFICATION"
        connection_state["cleanup_message"] = "Billing extraction completed, but automatic cleanup could not be verified. Please check your TNEB account manually."
        print(f"   ⚠ {connection_state['cleanup_message']}")
        
    return connection_state

async def delete_consumer_number(page, consumer_no: str, user_id: str = "") -> bool:
    """Backward-compatible helper wrapping safe_cleanup_consumer_number."""
    state = {
        "requested_consumer_number": normalize_consumer_number(consumer_no),
        "added_by_current_extraction": True,
        "is_primary_connection": False,
        "was_registered_before_extraction": False
    }
    res = await safe_cleanup_consumer_number(page, state, user_id=user_id)
    return res.get("cleanup_completed", False)

def parse_detconws_page(html: str, text: str, default_conn_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Extracts all consumer specifications, meter details, dues, and past 24 billing cycles."""
    data = {
        "consumer_name": "",
        "consumer_no": "",
        "region": "",
        "circle": "",
        "section": "",
        "distribution": "",
        "service_number": "",
        "sanctioned_load": "",
        "sanctioned_load_kw": 0.0,
        "phase": "",
        "tariff_code": "",
        "meter_number": "",
        "service_status": "LIVE",
        "address": "",
        "aadhar_status": "",
        "dues": {
            "has_dues": False,
            "bill_month": "",
            "bill_year": "",
            "amount": 0.0,
            "due_date": "",
            "description": ""
        },
        "billing_cycles": []
    }
    
    trs = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL | re.IGNORECASE)
    
    for tr in trs:
        tds = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, re.DOTALL | re.IGNORECASE)
        cleaned = [re.sub(r'<[^>]+>', ' ', t).replace('&nbsp;', ' ').replace('-->', '').replace('<!--', '').strip() for t in tds]
        row_text = ' '.join(cleaned)
        
        # 1. Consumer Name & Consumer Number
        if 'CONSUMER NAME' in row_text:
            m_name = re.search(r'CONSUMER\s*NAME\s*:\s*(.*?)(?=\s*CONSUMER\s*NUMBER|$)', row_text, re.I)
            m_num = re.search(r'CONSUMER\s*NUMBER\s*:\s*([0-9]+)', row_text, re.I)
            if m_name and m_name.group(1).strip():
                data['consumer_name'] = m_name.group(1).strip()
            if m_num and m_num.group(1).strip():
                data['consumer_no'] = m_num.group(1).strip()
                
        # 2. Key-value cell scanning
        for i in range(len(cleaned)):
            cell = cleaned[i].upper()
            if cell == 'REGION' and i+1 < len(cleaned) and cleaned[i+1]:
                data['region'] = cleaned[i+1]
            elif cell == 'CIRCLE' and i+1 < len(cleaned) and cleaned[i+1]:
                data['circle'] = cleaned[i+1]
            elif cell == 'SECTION' and i+1 < len(cleaned) and cleaned[i+1]:
                data['section'] = cleaned[i+1]
            elif cell == 'DISTRIBUTION' and i+1 < len(cleaned) and cleaned[i+1]:
                data['distribution'] = cleaned[i+1]
            elif cell == 'SERVICE NUMBER' and i+1 < len(cleaned) and cleaned[i+1]:
                data['service_number'] = cleaned[i+1]
            elif cell == 'PHASE' and i+1 < len(cleaned) and cleaned[i+1]:
                data['phase'] = f"{cleaned[i+1]} Phase"
            elif cell == 'SANCTIONED LOAD' and i+1 < len(cleaned) and cleaned[i+1]:
                data['sanctioned_load'] = cleaned[i+1]
                num_m = re.search(r'\d+(\.\d+)?', cleaned[i+1])
                if num_m: data['sanctioned_load_kw'] = float(num_m.group(0))
            elif cell == 'METER NUMBER' and i+1 < len(cleaned) and cleaned[i+1]:
                data['meter_number'] = cleaned[i+1]
            elif cell == 'ADDRESS' and i+1 < len(cleaned) and cleaned[i+1]:
                data['address'] = cleaned[i+1]
            elif cell == 'SERVICE STATUS' and i+1 < len(cleaned) and cleaned[i+1]:
                data['service_status'] = cleaned[i+1]
            elif cell == 'TARIFF CODE' and i+1 < len(cleaned) and cleaned[i+1]:
                data['tariff_code'] = cleaned[i+1]
            elif cell == 'AADHAR' and i+1 < len(cleaned) and cleaned[i+1]:
                data['aadhar_status'] = cleaned[i+1]
                
        # 3. Dues Row check
        if len(cleaned) >= 6 and re.match(r'^\d{2}$', cleaned[0]) and re.match(r'^\d{4}$', cleaned[1]):
            try:
                amt = float(cleaned[3].replace(',', '')) if len(cleaned) > 3 and cleaned[3] else 0.0
                if amt > 0:
                    data['dues'] = {
                        'has_dues': True,
                        'bill_month': cleaned[0],
                        'bill_year': cleaned[1],
                        'acct_desc': cleaned[2] if len(cleaned) > 2 else '',
                        'amount': amt,
                        'due_date': cleaned[4] if len(cleaned) > 4 else '',
                        'description': cleaned[5] if len(cleaned) > 5 else ''
                    }
            except Exception:
                pass
                
        # 4. Billing Cycles Rows
        if len(cleaned) >= 8 and re.match(r'^\d{2}/\d{2}/\d{4}$', cleaned[0]):
            try:
                cycle_data = {
                    'assessment_date': cleaned[0],
                    'entry_date': cleaned[1] if len(cleaned) > 1 else '',
                    'status': cleaned[2] if len(cleaned) > 2 else 'NORMAL',
                    'kwh_reading': float(cleaned[3].replace(',', '')) if len(cleaned) > 3 and cleaned[3] else 0.0,
                    'kvah_reading': float(cleaned[4].replace(',', '')) if len(cleaned) > 4 and cleaned[4] else None,
                    'recorded_demand': float(cleaned[5].replace(',', '')) if len(cleaned) > 5 and cleaned[5] else 0.0,
                    'units_consumed': float(cleaned[7].replace(',', '')) if len(cleaned) > 7 and cleaned[7] else 0.0,
                    'cc_charges': float(cleaned[8].replace(',', '')) if len(cleaned) > 8 and cleaned[8] else 0.0,
                    'electricity_tax': float(cleaned[9].replace(',', '')) if len(cleaned) > 9 and cleaned[9] else 0.0,
                    'fixed_charges': float(cleaned[13].replace(',', '')) if len(cleaned) > 13 and cleaned[13] else 0.0,
                    'total_charges': float(cleaned[14].replace(',', '')) if len(cleaned) > 14 and cleaned[14] else 0.0,
                    'amount_to_be_paid': float(cleaned[17].replace(',', '')) if len(cleaned) > 17 and cleaned[17] else 0.0,
                    'due_date': cleaned[18] if len(cleaned) > 18 else '',
                    'amount_paid': float(cleaned[19].replace(',', '')) if len(cleaned) > 19 and cleaned[19] else 0.0,
                    'receipt_no': cleaned[20].replace('-->', '').replace('<!--', '').strip() if len(cleaned) > 20 else '',
                    'payment_date': cleaned[21] if len(cleaned) > 21 else ''
                }
                data['billing_cycles'].append(cycle_data)
            except Exception:
                pass
                
    # Fallback to default_conn_info if any specification was blank
    if default_conn_info:
        if not data["consumer_no"]:
            data["consumer_no"] = default_conn_info.get("consumer_no", "")
        if not data["consumer_name"]:
            data["consumer_name"] = default_conn_info.get("name", "")
        if not data["address"]:
            data["address"] = default_conn_info.get("address", "")
        if not data["service_status"]:
            data["service_status"] = default_conn_info.get("status", "LIVE")
            
    # 5. Solar Capacity Analysis
    # Formula: Past 6 cycle units / 1500 = Solar capacity load requirements (kW)
    past_6 = data["billing_cycles"][:6]
    past_6_units = [c['units_consumed'] for c in past_6]
    total_6_cycle_units = round(sum(past_6_units), 2)
    bi_monthly_avg = round(total_6_cycle_units / len(past_6), 2) if past_6 else 0.0
    
    solar_capacity_req_kw = round(total_6_cycle_units / 1500.0, 2) if total_6_cycle_units > 0 else 0.0
    recommended_solar_kw = round(solar_capacity_req_kw * 2) / 2 if solar_capacity_req_kw >= 1.0 else solar_capacity_req_kw
    
    panel_rating_wp = 540
    panel_count = math.ceil((solar_capacity_req_kw * 1000) / panel_rating_wp) if solar_capacity_req_kw > 0 else 0
    roof_area_sqft = round(solar_capacity_req_kw * 100) if solar_capacity_req_kw > 0 else 0
    estimated_annual_gen = round(solar_capacity_req_kw * 1500, 1)
    
    sanctioned_kw = data.get("sanctioned_load_kw", 0.0)
    net_meter_compliant = (solar_capacity_req_kw <= sanctioned_kw) if sanctioned_kw > 0 else True
    
    data["solar_analysis"] = {
        "formula": "Past 6 Cycle Units / 1500",
        "past_6_cycles_units": past_6_units,
        "total_6_cycles_units": total_6_cycle_units,
        "bi_monthly_avg_units": bi_monthly_avg,
        "divisor": 1500,
        "solar_capacity_required_kw": solar_capacity_req_kw,
        "recommended_solar_kw": recommended_solar_kw,
        "panel_rating_wp": panel_rating_wp,
        "estimated_panel_count": panel_count,
        "estimated_roof_area_sqft": roof_area_sqft,
        "estimated_annual_generation_kwh": estimated_annual_gen,
        "sanctioned_load_kw": sanctioned_kw,
        "net_meter_compliant": net_meter_compliant
    }
            
    return data

def print_terminal_report(data: Dict[str, Any]):
    """Prints a structured, high-visibility report directly to the terminal."""
    W = 78
    print("\n" + "=" * W)
    print(f"  TNEB OFFICIAL CONSUMER ACCOUNT & BILLING REPORT".center(W))
    print(f"  Source: TNPDCL Live Portal (detconws.php) • Date: {datetime.now().strftime('%d-%b-%Y %H:%M')}".center(W))
    print("=" * W)
    
    print("\n[1] CONNECTION SPECIFICATIONS")
    print("-" * W)
    print(f"  Consumer Name    : {data['consumer_name']}")
    print(f"  Consumer Number  : {data['consumer_no']}")
    print(f"  Address          : {data['address']}")
    print(f"  Region / Circle  : {data['region']} / {data['circle']}")
    print(f"  Section          : {data['section']}")
    print(f"  Distribution / SC: {data['distribution']} / {data['service_number']}")
    print(f"  Sanctioned Load  : {data['sanctioned_load']} ({data['phase']})")
    print(f"  Tariff Code      : {data['tariff_code']}")
    print(f"  Meter Number     : {data['meter_number']}")
    print(f"  Service Status   : {data['service_status']}")
    
    print("\n[2] CURRENT DUES STATUS")
    print("-" * W)
    if data["dues"]["has_dues"]:
        print(f"  Outstanding Bill : Month {data['dues']['bill_month']}/{data['dues']['bill_year']}")
        print(f"  Payable Amount   : Rs. {data['dues']['amount']:,.2f}")
        print(f"  Due Date         : {data['dues']['due_date']}")
    else:
        print("  Outstanding Bill : NIL / All dues cleared")
        
    print(f"\n[3] PAST BILLING CYCLES LEDGER ({len(data['billing_cycles'])} Records Extracted)")
    print("-" * W)
    print(f"  {'Date':<12} | {'Reading':<9} | {'Demand':<7} | {'Units (kWh)':<12} | {'CC Charges':<11} | {'Paid Date':<11}")
    print("-" * W)
    
    for c in data["billing_cycles"][:12]:
        p_date = c['payment_date'] or "-"
        print(f"  {c['assessment_date']:<12} | {c['kwh_reading']:<9.1f} | {c['recorded_demand']:<7.2f} | {c['units_consumed']:<12.1f} | Rs {c['cc_charges']:<8.1f} | {p_date:<11}")
        
    if len(data["billing_cycles"]) > 12:
        print(f"  ... and {len(data['billing_cycles']) - 12} older billing cycles preserved.")
        
    # 6-Cycle Summary
    past_6 = [c['units_consumed'] for c in data['billing_cycles'][:6]]
    if past_6:
        total_6 = sum(past_6)
        avg_6 = total_6 / len(past_6)
        print("-" * W)
        print(f"  PAST 6-CYCLES SUMMARY : {past_6}")
        print(f"  TOTAL 6-CYCLE UNITS   : {total_6:,.1f} kWh")
        print(f"  BI-MONTHLY AVERAGE    : {avg_6:,.1f} kWh / cycle")
        print(f"  ESTIMATED ANNUAL USAGE: {avg_6 * 6:,.1f} kWh / year")
        
    # [4] SOLAR CAPACITY REQUIREMENTS (FORMULA: UNITS ÷ 1500)
    sa = data.get("solar_analysis", {})
    if sa:
        print("\n[4] SOLAR CAPACITY REQUIREMENTS (FORMULA: UNITS ÷ 1500)")
        print("-" * W)
        print(f"  Past 6-Cycles Units   : {sa.get('total_6_cycles_units', 0):,.1f} kWh (1 Year Bi-Monthly)")
        print(f"  Calculation Formula   : Past 6 Cycle Units ÷ 1500")
        print(f"  Solar Capacity Req.   : {sa.get('solar_capacity_required_kw', 0):.2f} kW  (Recommended: {sa.get('recommended_solar_kw', 0):.1f} kW)")
        print(f"  Estimated Solar Panels: {sa.get('estimated_panel_count', 0)} × {sa.get('panel_rating_wp', 540)}Wp Mono PERC Modules")
        print(f"  Shadow-Free Roof Area : ~{sa.get('estimated_roof_area_sqft', 0)} sq.ft")
        print(f"  Annual Generation Est.: ~{sa.get('estimated_annual_generation_kwh', 0):,.1f} kWh / year")
        sanct = sa.get("sanctioned_load_kw", 0.0)
        if sanct > 0:
            pct = (sa.get('solar_capacity_required_kw', 0) / sanct) * 100
            comp = "✓ 100% Net-metering Compliant" if pct <= 100 else "⚠ Exceeds Sanctioned Load (Enhancement Recommended)"
            print(f"  Sanctioned Load Match : {sanct:.1f} KW ({pct:.1f}% ratio) • {comp}")
            
    # [5] CONNECTION LIFECYCLE & CLEANUP STATUS
    cs = data.get("connection_state", {})
    if cs:
        print("\n[5] CONNECTION LIFECYCLE & CLEANUP STATUS")
        print("-" * W)
        if cs.get("is_primary_connection"):
            c_type = "PRIMARY ACCOUNT CONNECTION (Protected by Portal Design)"
        elif cs.get("was_registered_before_extraction"):
            c_type = "PRE-EXISTING SECONDARY (Retained on Account)"
        else:
            c_type = "TEMPORARY SECONDARY (Added by Current Extraction)"
        print(f"  Connection Type  : {c_type}")
        print(f"  Cleanup Action   : {cs.get('cleanup_status', 'N/A')}")
        print(f"  Audit Status     : {cs.get('cleanup_message', 'No action performed.')}")
    print("=" * W + "\n")

def save_markdown_and_json_report(data: Dict[str, Any], target_dir: str):
    """Saves both JSON and Markdown report files for the consumer."""
    os.makedirs(target_dir, exist_ok=True)
    c_no = data.get("consumer_no") or "unknown"
    
    # 1. JSON
    json_path = os.path.join(target_dir, f"tneb_report_{c_no}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    # 2. Markdown
    md_path = os.path.join(target_dir, f"tneb_report_{c_no}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# TNEB Official Consumer Account & Billing Report\n\n")
        f.write(f"**Extracted On:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n")
        f.write(f"**Portal URL:** {LOGIN_URL}  \n\n")
        f.write(f"## 1. Consumer & Service Specifications\n\n")
        f.write(f"| Field | Value |\n|---|---|\n")
        f.write(f"| **Consumer Name** | `{data['consumer_name']}` |\n")
        f.write(f"| **Consumer Number** | `{data['consumer_no']}` |\n")
        f.write(f"| **Address** | {data['address']} |\n")
        f.write(f"| **Region / Circle** | {data['region']} / {data['circle']} |\n")
        f.write(f"| **Section** | {data['section']} |\n")
        f.write(f"| **Distribution / Service** | {data['distribution']} / {data['service_number']} |\n")
        f.write(f"| **Sanctioned Load** | {data['sanctioned_load']} ({data['phase']}) |\n")
        f.write(f"| **Tariff Code** | {data['tariff_code']} |\n")
        f.write(f"| **Meter Number** | {data['meter_number']} |\n")
        f.write(f"| **Service Status** | `{data['service_status']}` |\n\n")
        
        f.write(f"## 2. Current Dues\n\n")
        if data["dues"]["has_dues"]:
            f.write(f"- **Bill Period:** {data['dues']['bill_month']}/{data['dues']['bill_year']}\n")
            f.write(f"- **Amount Payable:** ₹{data['dues']['amount']:,.2f}\n")
            f.write(f"- **Due Date:** {data['dues']['due_date']}\n")
        else:
            f.write(f"- **Current Dues:** Nil / Clear\n\n")
            
        f.write(f"## 3. Past Billing History ({len(data['billing_cycles'])} Cycles)\n\n")
        f.write(f"| Assessment Date | KWH Reading | Recorded Demand | Units (kWh) | CC Charges (₹) | Paid Date | Receipt No |\n")
        f.write(f"|---|---|---|---|---|---|---|\n")
        for c in data["billing_cycles"]:
            f.write(f"| {c['assessment_date']} | {c['kwh_reading']} | {c['recorded_demand']} | **{c['units_consumed']}** | ₹{c['cc_charges']} | {c['payment_date']} | {c['receipt_no']} |\n")
            
        # 4. Solar Capacity Requirements
        sa = data.get("solar_analysis", {})
        if sa:
            f.write(f"\n## 4. Solar Capacity Requirements (System Sizing)\n\n")
            f.write(f"| Sizing Parameter | Value |\n|---|---|\n")
            f.write(f"| **Calculation Formula** | `Past 6 Cycles Units ÷ 1500 = Solar Capacity (kW)` |\n")
            f.write(f"| **Past 6 Cycles Consumption** | **{sa.get('total_6_cycles_units', 0):,.1f} kWh** |\n")
            f.write(f"| **Bi-Monthly Average** | {sa.get('bi_monthly_avg_units', 0):,.1f} kWh / cycle |\n")
            f.write(f"| **Calculated Solar Capacity** | **`{sa.get('solar_capacity_required_kw', 0):.2f} kW`** |\n")
            f.write(f"| **Recommended System Size** | **{sa.get('recommended_solar_kw', 0):.1f} kW** |\n")
            f.write(f"| **Estimated Solar Panels** | {sa.get('estimated_panel_count', 0)} × {sa.get('panel_rating_wp', 540)}Wp Mono PERC Modules |\n")
            f.write(f"| **Shadow-Free Roof Area** | ~{sa.get('estimated_roof_area_sqft', 0)} sq.ft |\n")
            f.write(f"| **Estimated Annual Generation** | ~{sa.get('estimated_annual_generation_kwh', 0):,.1f} kWh / year |\n")
            sanct = sa.get("sanctioned_load_kw", 0.0)
            if sanct > 0:
                pct = (sa.get('solar_capacity_required_kw', 0) / sanct) * 100
                comp = "✓ 100% Net-metering Compliant (Within Sanctioned Load)" if pct <= 100 else "⚠ Exceeds Sanctioned Load (Enhancement Recommended)"
                f.write(f"| **Sanctioned Load Match** | {sanct:.1f} KW ({pct:.1f}% ratio) • {comp} |\n\n")
            else:
                f.write("\n")
                
        # 5. Connection Lifecycle & Cleanup Protection Status
        cs = data.get("connection_state", {})
        if cs:
            f.write(f"## 5. Connection Lifecycle & Cleanup Protection Status\n\n")
            f.write(f"| Parameter | Value |\n|---|---|\n")
            if cs.get("is_primary_connection"):
                c_type = "Primary Account Connection (Protected by Portal Design)"
            elif cs.get("was_registered_before_extraction"):
                c_type = "Pre-Existing Secondary Connection (Retained on Account)"
            else:
                c_type = "Temporary Secondary Connection"
            f.write(f"| **Connection Type** | `{c_type}` |\n")
            f.write(f"| **Cleanup Status** | `{cs.get('cleanup_status', 'N/A')}` |\n")
            f.write(f"| **Audit Message** | {cs.get('cleanup_message', '')} |\n\n")
            
    print(f"Reports saved:")
    print(f" -> JSON: {json_path}")
    print(f" -> Markdown: {md_path}")

async def notify_cb(callback, step: str, message: str, status: str = "info", data: Any = None):
    if callback:
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(step, message, status, data)
            else:
                callback(step, message, status, data)
        except Exception:
            pass

async def main_async(consumer_no: str, user_id: str, password: str, headless: bool = True, delete_after: bool = True, callback=None) -> Dict[str, Any]:
    print("=" * 70)
    print("⚡ TNEB AUTOMATED ACCOUNT SUMMARY & LEDGER EXTRACTOR")
    print(f"Portal User ID: {user_id}")
    print(f"Target Consumer Number: {consumer_no}")
    print("=" * 70)
    
    # Initialize connection lifecycle & protection state
    connection_state = init_connection_state(consumer_no)
    clean_target = connection_state["requested_consumer_number"]
    
    await notify_cb(callback, "init", f"Initiating extraction for consumer {consumer_no} (User: {user_id})...", "progress")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()
        
        # Step 1: Login
        await notify_cb(callback, "login", f"Solving optical captcha & authenticating user '{user_id}'...", "progress")
        login_ok = await login_tneb(page, user_id=user_id, password=password)
        if not login_ok:
            await browser.close()
            await notify_cb(callback, "login", "TNEB authentication failed. Please verify your User ID, Password, and try again.", "error")
            return {"error": "Failed to log in to TNEB portal. Please verify your User ID and Password."}
            
        await notify_cb(callback, "login", f"Authenticated successfully as '{user_id}'!", "success")
            
        # Step 1.5: Pre-Extraction Registration Audit
        # Determine whether consumer is Primary, Pre-existing Secondary, or New Connection
        registered_map = await scan_registered_connections(page)
        
        if clean_target and clean_target in registered_map:
            reg_info = registered_map[clean_target]
            connection_state["was_registered_before_extraction"] = True
            if reg_info.get("is_primary"):
                connection_state["is_primary_connection"] = True
                connection_state["is_secondary_connection"] = False
                connection_state["cleanup_status"] = "RETAINED_PRIMARY"
                connection_state["cleanup_message"] = "Primary consumer connection detected. Your original TNEB connection has been retained."
                print(f"\n[Audit] Primary consumer connection detected: '{clean_target}' belongs to existing TNEB account and will be retained.")
            else:
                connection_state["is_primary_connection"] = False
                connection_state["is_secondary_connection"] = True
                connection_state["cleanup_status"] = "RETAINED_PREEXISTING"
                connection_state["cleanup_message"] = "This consumer connection was already registered before extraction. It has been retained."
                print(f"\n[Audit] Existing secondary consumer connection detected: '{clean_target}' was already registered before extraction and will be retained.")
            
            # Connection already exists -> Skip addition step!
            conn_info = {
                "consumer_no": clean_target,
                "name": reg_info.get("consumer_name", ""),
                "address": "Registered Account Connection",
                "status": "Live",
                "was_added": False
            }
            await notify_cb(callback, "add", f"Existing registered connection confirmed: {clean_target} ({conn_info.get('name', '')})", "success")
        else:
            # Step 2: New Connection -> Add number & Confirm
            connection_state["was_registered_before_extraction"] = False
            connection_state["is_primary_connection"] = False
            await notify_cb(callback, "add", f"Adding consumer {consumer_no} to account & verifying details...", "progress")
            conn_info = await add_consumer_number(page, consumer_no)
            if conn_info.get("was_added"):
                connection_state["added_by_current_extraction"] = True
                connection_state["is_secondary_connection"] = True
                await notify_cb(callback, "add", f"Verified & confirmed new connection: {conn_info.get('name', '')} ({conn_info.get('status', 'Live')})", "success")
            else:
                connection_state["added_by_current_extraction"] = False
                connection_state["was_registered_before_extraction"] = True
                connection_state["cleanup_status"] = "RETAINED_PREEXISTING"
                connection_state["cleanup_message"] = "This consumer connection was already registered before extraction. It has been retained."
                await notify_cb(callback, "add", f"Connection already registered: {conn_info.get('name', '')}", "success")
        
        # Step 3: Account Summary & Detconws extraction
        await notify_cb(callback, "summary", "Navigating to Account Summary and opening detailed ledger...", "progress")
        result_data = await extract_account_summary_and_details(context, page, consumer_no, conn_info=conn_info)
        
        # Stop immediately if consumer was not found or verification failed
        if result_data.get("error"):
            connection_state["extraction_completed"] = False
            err_title = result_data.get("title", "Extraction Error")
            err_msg = result_data["error"]
            print(f"\n" + "=" * 70)
            print(f"❌ [{err_title.upper()}]")
            print(f"{err_msg}")
            print("=" * 70 + "\n")
            
            # Scenario D: If extraction fails after adding a temporary connection, attempt cleanup ONLY for this temporary connection!
            if delete_after and connection_state.get("added_by_current_extraction"):
                print(f"   [Cleanup] Extraction failed. Performing safe cleanup of newly added temporary connection '{clean_target}'...")
                await notify_cb(callback, "delete", f"Extraction stopped. Performing safe cleanup of temporary connection {clean_target}...", "progress")
                await safe_cleanup_consumer_number(page, connection_state, user_id=user_id)
                await notify_cb(callback, "delete", connection_state["cleanup_message"], "info", data=connection_state)
            else:
                if connection_state.get("is_primary_connection") or connection_state.get("was_registered_before_extraction"):
                    print(f"   [Cleanup Protection] {connection_state['cleanup_message']}")
                    
            await notify_cb(callback, "summary", err_msg, "error", data={"title": err_title, "error": err_msg, "consumer_no": consumer_no})
            await browser.close()
            return result_data
            
        connection_state["extraction_completed"] = True
        result_data["connection_state"] = connection_state
            
        # Step 4: Display and Save Report ONLY for verified exact match
        print_terminal_report(result_data)
        save_markdown_and_json_report(result_data, "/Users/karthik/tneb-account-extractor")
        await notify_cb(callback, "report", f"Extracted {len(result_data.get('billing_cycles', []))} billing cycles successfully!", "success", data=result_data)
        
        # Step 5: Safe Cleanup with Primary & Pre-Existing Account Protection
        if not delete_after:
            connection_state["cleanup_status"] = "NOT_REQUIRED"
            connection_state["cleanup_message"] = "Connection retained per user configuration (--keep)."
            print(f"\n[Cleanup] {connection_state['cleanup_message']}")
            await notify_cb(callback, "delete", connection_state["cleanup_message"], "info", data=connection_state)
        else:
            await notify_cb(callback, "delete", "Evaluating connection lifecycle & executing safe cleanup...", "progress")
            await safe_cleanup_consumer_number(page, connection_state, user_id=user_id)
            status_type = "success" if connection_state["cleanup_status"] in ["RETAINED_PRIMARY", "RETAINED_PREEXISTING", "SUCCESS_REMOVED"] else "warning"
            await notify_cb(callback, "delete", connection_state["cleanup_message"], status_type, data=connection_state)
            
        result_data["connection_state"] = connection_state
        await browser.close()
        print("\nAll steps completed successfully!")
        await notify_cb(callback, "done", "Extraction pipeline completed successfully!", "done", data=result_data)
        return result_data

def main():
    import getpass
    parser = argparse.ArgumentParser(description="TNEB Auto Login, Add Consumer Number, Account Summary Extractor & Auto-Delete")
    parser.add_argument("--user-id", "-u", type=str, default=None, help="TNEB Portal User ID (e.g. karthice1)")
    parser.add_argument("--password", "-p", type=str, default=None, help="TNEB Portal Password")
    parser.add_argument("--consumer-no", "-c", type=str, default=None, help="TNEB Service Connection Number (e.g. 044060072111)")
    parser.add_argument("--headed", action="store_true", help="Run browser in visible/headed mode")
    parser.add_argument("--keep", action="store_true", help="Keep the consumer number in TNEB account (do not delete after fetching)")
    args = parser.parse_args()
    
    user_id = args.user_id
    if not user_id:
        user_id = input("Enter TNEB User ID: ").strip()
    if not user_id:
        print("Error: TNEB User ID cannot be empty.")
        sys.exit(1)
        
    password = args.password
    if not password:
        try:
            password = getpass.getpass("Enter TNEB Password: ").strip()
        except Exception:
            password = input("Enter TNEB Password: ").strip()
    if not password:
        print("Error: TNEB Password cannot be empty.")
        sys.exit(1)
        
    c_no = args.consumer_no
    if not c_no:
        c_no = input("Enter TNEB Consumer Number to Add and View Summary: ").strip()
    if not c_no:
        print("Error: Consumer number cannot be empty.")
        sys.exit(1)
        
    result = asyncio.run(main_async(c_no, user_id=user_id, password=password, headless=not args.headed, delete_after=not args.keep))
    if result.get("error"):
        sys.exit(1)

if __name__ == "__main__":
    main()
