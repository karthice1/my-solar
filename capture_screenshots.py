import os
import sys
import json
import time
from playwright.sync_api import sync_playwright

ARTIFACT_DIR = "/Users/karthik/.gemini/antigravity-cli/brain/dd275a14-3e0a-41cc-be99-7b5230151074/screenshots"
os.makedirs(ARTIFACT_DIR, exist_ok=True)

def capture_ui_and_pdf():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 950})
        page = context.new_page()

        # 1. Open Web Application
        print("Navigating to dashboard...")
        page.goto("http://127.0.0.1:8090/")
        page.wait_for_timeout(1000)

        # 2. Quotation Settings (Authenticate PIN)
        print("Capturing Quotation Settings...")
        page.click("button:has-text('Quotation Settings')")
        page.wait_for_timeout(500)
        
        # Fill PIN modal if visible
        pin_input = page.locator("input[placeholder='Enter owner PIN']")
        if pin_input.is_visible():
            pin_input.fill("1234")
            page.click("button:has-text('Unlock Settings')")
            page.wait_for_timeout(1000)
        
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "01_quotation_settings.png"), full_page=True)
        print("-> Saved 01_quotation_settings.png")

        # 3. Quotation History
        print("Capturing Quotation History...")
        page.click("button:has-text('Quotation History')")
        page.wait_for_timeout(1000)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "02_quotation_history.png"), full_page=True)
        print("-> Saved 02_quotation_history.png")

        # 4. Quotation Builder (Generate for 044060072111)
        print("Generating quotation for consumer 044060072111...")
        page.click("button:has-text('Quotation Builder')")
        page.wait_for_timeout(500)
        
        # Load quotation via Alpine data
        page.evaluate("() => { const d = Alpine.$data(document.querySelector('body')); d.activeNav = 'builder'; d.loadQuotationForConsumer('044060072111'); }")
        page.wait_for_timeout(2500)
        
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "03_quotation_builder_live.png"), full_page=False)
        print("-> Saved 03_quotation_builder_live.png")

        # 5. Three Tiered Packages Tab
        print("Capturing Packages Comparison...")
        page.evaluate("() => { const d = Alpine.$data(document.querySelector('body')); d.builderTab = 'packages'; }")
        page.wait_for_timeout(1000)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "04_quotation_packages.png"), full_page=True)
        print("-> Saved 04_quotation_packages.png")

        # 6. Render 5-page PDF Quotation HTML directly in browser and capture each page
        print("Capturing 5-Page Quotation Proposal...")
        from quotation.quotation_history import get_quotation
        from quotation.pdf_generator import env, format_inr, format_num

        quotation = get_quotation("RENSUN/2026/0001")
        if quotation:
            template = env.get_template("quotation.html")
            rendered_html = template.render(
                q=quotation,
                format_inr=format_inr,
                format_num=format_num
            )
            
            pdf_page = context.new_page()
            pdf_page.set_viewport_size({"width": 960, "height": 1360})
            pdf_page.set_content(rendered_html)
            pdf_page.wait_for_timeout(1500)
            
            pages = pdf_page.locator(".page").all()
            for idx, p_elem in enumerate(pages, start=1):
                img_path = os.path.join(ARTIFACT_DIR, f"proposal_page_{idx}.png")
                p_elem.screenshot(path=img_path)
                print(f"-> Saved proposal_page_{idx}.png")
                
            pdf_page.close()

        browser.close()
        print("All visual proof artifacts captured successfully!")

if __name__ == "__main__":
    capture_ui_and_pdf()
