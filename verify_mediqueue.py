import asyncio
from playwright.async_api import async_playwright
import os

async def run_verification():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()

        # 1. Landing Page
        print("Checking Landing Page...")
        await page.goto("http://localhost:5000/")
        await page.wait_for_selector("text=I'm a Patient")
        await page.wait_for_selector("text=I'm a Doctor / Hospital Staff")
        await page.wait_for_selector("button:has-text('Try Demo')")
        await page.screenshot(path="landing.png")
        print("Landing page OK.")

        # 2. Try Demo Flow
        print("Checking Try Demo flow...")
        await page.click("button:has-text('Try Demo')")

        await page.wait_for_selector("#view-patient.active")
        await page.wait_for_selector("#screen-4.active")

        # Check specific values set by tryDemo()
        pos = await page.inner_text("#live-pos")
        eta = await page.inner_text("#live-eta")
        print(f"Demo Stats - Position: {pos}, ETA: {eta}")

        assert pos == "3"
        assert "18 min" in eta

        await page.screenshot(path="demo_dashboard.png")
        print("Try Demo OK.")

        # 3. Hospital Discovery
        print("Checking Hospital Discovery...")
        await page.click("#screen-4 >> text=Find Hospitals Near Me 📍")
        await page.wait_for_selector("#screen-5.active")

        await context.grant_permissions(["geolocation"], origin="http://localhost:5000")
        await context.set_geolocation({"latitude": 17.4326, "longitude": 78.4071}) # Near Apollo Jubilee Hills

        await page.click("id=disc-btn")
        await page.wait_for_selector(".hospital-card", timeout=10000)

        h_names = await page.eval_on_selector_all(".h-name", "nodes => nodes.map(n => n.innerText)")
        print(f"Found hospitals: {h_names[:3]}")
        assert any("Apollo" in name for name in h_names)

        await page.screenshot(path="discovery.png")
        print("Hospital Discovery OK.")

        # 4. Patient Login & Signup
        print("Checking Auth Pages...")
        await page.goto("http://localhost:5000/patient/login")
        await page.wait_for_selector("text=Patient Login")
        await page.click("text=Create account")
        await page.wait_for_selector("text=Patient Signup")
        await page.screenshot(path="patient_auth.png")
        print("Patient Auth OK.")

        # 5. Hospital Portal
        print("Checking Hospital Portal...")
        await page.goto("http://localhost:5000/hospital/login")
        await page.wait_for_selector("text=Hospital Portal")
        await page.fill("id=hl-name", "Apollo Clinic")
        await page.fill("id=hl-user", "DR-777")
        await page.fill("id=hl-code", "HOSP-001")
        await page.click("button:has-text('Login to Portal')")

        await page.wait_for_selector("#view-hospital.active")

        # Trigger GPS Cascade Demo
        await page.fill("id=action-id", "MQ-DEMO")
        await page.click("text=Trigger GPS Cascade")

        # Specific selector for cascade results to avoid conflict with doctor name in dropdown
        await page.wait_for_selector("#cascade-result >> text=Ravi Kumar")
        await page.wait_for_selector("#cascade-result >> text=Sunita Devi")
        await page.wait_for_selector("#cascade-result >> text=Arjun Reddy")

        await page.screenshot(path="hospital_dashboard_cascade.png")
        print("Hospital Dashboard & Cascade OK.")

        await browser.close()
        print("Verification Complete.")

if __name__ == "__main__":
    asyncio.run(run_verification())
