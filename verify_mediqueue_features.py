import asyncio
from playwright.async_api import async_playwright
import time
import subprocess
import os

async def verify_mediqueue():
    # Start the Flask server
    server_process = subprocess.Popen(["python3", "app.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(3) # Wait for server to start

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # 1. Verify Landing Page
            print("Verifying Landing Page...")
            await page.goto("http://127.0.0.1:5000/")
            await page.wait_for_selector("#view-landing .logo", state="visible")
            await page.wait_for_selector("text=I'm a Patient")
            await page.wait_for_selector("text=I'm a Doctor / Hospital Staff")
            await page.wait_for_selector("text=Try Demo")
            await page.wait_for_selector("text=Prototype — built for Startup Aid 2026")
            await page.screenshot(path="verification/landing.png")

            # 2. Verify Try Demo
            print("Verifying Try Demo...")
            await page.click("text=Try Demo")
            await page.wait_for_selector("#view-patient.active")
            await page.wait_for_selector("#view-patient #screen-4.active h2:has-text('Live Queue')")
            # Ravi Kumar should be visible in the live queue panel text or some other way if #p-name is hidden
            await page.wait_for_selector("#view-patient #screen-4.active .live-eta:has-text('Approx. 18 min wait')")
            await page.screenshot(path="verification/patient_dashboard_demo.png")

            # 3. Verify Patient Login Page
            print("Verifying Patient Login Page...")
            await page.click("#main-nav button:has-text('Logout')")
            await page.click("text=I'm a Patient")
            await page.wait_for_selector("#view-patient-login.active")
            await page.click("text=Back to home")
            await page.wait_for_selector("#view-landing.active")

            # 4. Verify Hospital Discovery
            print("Verifying Hospital Discovery...")
            await page.click("text=Try Demo")
            await page.wait_for_selector("#view-patient #screen-4.active .cta:has-text('Find Hospitals Near Me')", state="visible")
            await page.click("#view-patient #screen-4.active .cta:has-text('Find Hospitals Near Me')")
            await page.wait_for_selector("#screen-5.active")
            # Mocking geolocation is complex in this setup, but we can check if the UI elements are there
            await page.wait_for_selector("text=Find Nearby")
            await page.screenshot(path="verification/hospital_discovery.png")

            # 5. Verify Hospital Login and GPS Cascade
            print("Verifying Hospital Dashboard & GPS Cascade...")
            await page.click("#main-nav button:has-text('Logout')")
            await page.click("text=I'm a Doctor / Hospital Staff")
            await page.wait_for_selector("#view-hospital-login.active")
            await page.fill("#hl-name", "Apollo Clinic")
            await page.fill("#hl-user", "DR-123")
            await page.fill("#hl-code", "HOSP-001")
            await page.fill("#hl-pass", "password")
            await page.click("text=Login to Portal")
            await page.wait_for_selector("#view-hospital.active")

            await page.fill("#action-id", "MQ-TEST")
            await page.click("text=Trigger GPS Cascade")
            await page.wait_for_selector("#cascade-result span:has-text('Ravi Kumar')")
            await page.wait_for_selector(".badge-demo.notified:has-text('Notified')")
            await page.wait_for_selector("text=Pending")
            await page.wait_for_selector("text=Standby")
            await page.screenshot(path="verification/hospital_dashboard_cascade.png")

            print("All verifications passed!")

        except Exception as e:
            print(f"Verification failed: {e}")
            await page.screenshot(path="verification/error.png")
            raise e
        finally:
            await browser.close()
            server_process.terminate()

if __name__ == "__main__":
    if not os.path.exists("verification"):
        os.makedirs("verification")
    asyncio.run(verify_mediqueue())
