"""PDF Generator: Pixel-Perfect HTML/CSS to PDF Generation Using Playwright Chromium.

Generates 5-page commercial solar proposals with strict Indian numbering/currency formatting,
custom branding, and clean page breaks.
"""

import os
import re
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader
from playwright.async_api import async_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
OUTPUT_PDF_DIR = os.path.join(BASE_DIR, "generated_quotations")
os.makedirs(OUTPUT_PDF_DIR, exist_ok=True)

def format_inr(value: Any) -> str:
    """Formats float or int into Indian Rupee string: e.g. ₹ 1,50,000 or ₹ 78,000."""
    try:
        val = float(value or 0.0)
    except (ValueError, TypeError):
        return "₹ 0"

    is_negative = val < 0
    val = abs(val)

    int_part = int(round(val))
    s = str(int_part)
    
    if len(s) <= 3:
        formatted = s
    else:
        last3 = s[-3:]
        remaining = s[:-3]
        # Group in pairs of 2 from right to left
        groups = []
        while len(remaining) > 2:
            groups.append(remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.append(remaining)
        groups.reverse()
        formatted = ",".join(groups) + "," + last3

    prefix = "- ₹ " if is_negative else "₹ "
    return prefix + formatted

def format_num(value: Any) -> str:
    """Formats float or int into Indian number formatting with commas."""
    try:
        val = float(value or 0.0)
    except (ValueError, TypeError):
        return "0"

    if val.is_integer():
        int_part = int(val)
        dec_part = ""
    else:
        int_part = int(val)
        dec_part = f".{int(round((val - int_part) * 10)):01d}"

    s = str(abs(int_part))
    if len(s) <= 3:
        formatted = s
    else:
        last3 = s[-3:]
        remaining = s[:-3]
        groups = []
        while len(remaining) > 2:
            groups.append(remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.append(remaining)
        groups.reverse()
        formatted = ",".join(groups) + "," + last3

    sign = "-" if val < 0 else ""
    return sign + formatted + dec_part

env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
env.filters["format_inr"] = format_inr
env.filters["format_num"] = format_num

async def render_quotation_html(quotation_data: Dict[str, Any]) -> str:
    """Renders quotation data into the full HTML string."""
    template = env.get_template("quotation.html")
    return template.render(
        q=quotation_data,
        format_inr=format_inr,
        format_num=format_num
    )

async def generate_quotation_pdf(quotation_data: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Renders quotation HTML and compiles it to a 5-page PDF using Playwright Chromium.
    Returns the absolute path to the generated PDF.
    """
    q_no = quotation_data.get("quotation_no", "DRAFT")
    clean_no = re.sub(r'[^A-Za-z0-9]', '_', q_no)
    
    if not output_path:
        filename = f"quotation_{clean_no}.pdf"
        output_path = os.path.join(OUTPUT_PDF_DIR, filename)

    html_content = await render_quotation_html(quotation_data)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Load HTML content into headless chromium
        await page.set_content(html_content, wait_until="networkidle")
        
        # Print directly to PDF with zero margin (CSS manages 18mm page margin)
        await page.pdf(
            path=output_path,
            format="A4",
            print_background=True,
            margin={"top": "0mm", "bottom": "0mm", "left": "0mm", "right": "0mm"}
        )
        await browser.close()

    quotation_data["pdf_path"] = output_path
    return output_path
