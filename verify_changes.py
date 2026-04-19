import os
import asyncio
from playwright.async_api import async_playwright
import time
import subprocess

async def run_verification():
    # Start the Flask server
    server_process = subprocess.Popen(['python3', 'app.py'])
    time.sleep(5) # Wait for server to start

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # 1. Landing Page Verification
            print("Verifying Landing Page...")
            await page.goto("http://localhost:5000")
            await page.wait_for_selector("#view-landing")

            # Check for "Prototype" badge
            footer_text = await page.inner_text("footer")
            if "Prototype — built for Startup Aid 2026" in footer_text:
                print("  - Footer badge present.")
            else:
                print("  - Footer badge MISSING.")

            # Check "I'm a Patient" button
            patient_btn = page.locator("button:has-text(\"I'm a Patient\")")
            await patient_btn.click()
            await page.wait_for_selector("#view-patient-login", state="visible")
            print("  - Patient Login navigation works.")

            await page.locator("#view-patient-login button:has-text(\"Back to home\")").click()

            # Check "I'm a Doctor" button
            doctor_btn = page.locator("button:has-text(\"I'm a Doctor / Hospital Staff\")")
            await doctor_btn.click()
            await page.wait_for_selector("#view-hospital-login", state="visible")
            print("  - Hospital Login navigation works.")

            await page.locator("#view-hospital-login button:has-text(\"Back to home\")").click()

            # 2. Try Demo Verification
            print("Verifying Try Demo...")
            demo_btn = page.locator("button:has-text(\"Try Demo\")")
            await demo_btn.click()
            await page.wait_for_selector("#view-patient", state="visible")
            await page.wait_for_selector("#screen-4", state="visible")
            print("  - Try Demo redirects to Patient Dashboard / Live Queue.")

            # 3. GPS Cascade Demo Verification
            print("Verifying GPS Cascade Demo...")
            await page.evaluate("switchView('hospital')")
            await page.wait_for_selector("#view-hospital", state="visible")

            await page.fill("#action-id", "MQ-TEST")
            await page.click("button:has-text(\"Trigger GPS Cascade\")")

            # Check for demo results
            await page.wait_for_selector("id=cascade-result >> text=Ravi Kumar")
            await page.wait_for_selector("id=cascade-result >> text=Sunita Devi")
            await page.wait_for_selector("id=cascade-result >> text=Arjun Reddy")
            print("  - GPS Cascade demo results visible.")

            # 4. Hospital Discovery Navigation
            print("Verifying Hospital Discovery UI...")
            await page.evaluate("switchView('patient')")
            await page.evaluate("gotoScreen(5)")
            await page.wait_for_selector("#screen-5", state="visible")
            print("  - Hospital Discovery screen accessible.")

            print("\nVerification successful!")

            await browser.close()
    finally:
        server_process.terminate()

if __name__ == "__main__":
    asyncio.run(run_verification())
