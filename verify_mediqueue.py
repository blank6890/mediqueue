import asyncio
from playwright.async_api import async_playwright
import os
import subprocess
import time

async def run_verification():
    # Start the Flask server
    server_process = subprocess.Popen(["python", "app.py"])
    time.sleep(2)  # Give the server time to start

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context()

            # Mock GPS location (Hyderabad)
            await context.set_geolocation({"latitude": 17.3850, "longitude": 78.4867})
            await context.grant_permissions(["geolocation"])

            page = await context.new_page()

            # 1. Test Landing Page
            print("Checking Landing Page...")
            await page.goto("http://127.0.0.1:5000")
            await page.wait_for_selector("text=Smart hospital")
            assert await page.is_visible("button:has-text(\"I'm a Patient\")")
            assert await page.is_visible("button:has-text(\"I'm a Doctor / Hospital Staff\")")
            assert await page.is_visible("button:has-text(\"Try Demo\")")
            print("Landing Page OK.")

            # 2. Test Patient Auth
            print("Checking Patient Login/Signup...")
            await page.click("button:has-text(\"I'm a Patient\")")
            assert page.url.endswith("/patient/login")
            await page.click("text=Create account")
            assert page.url.endswith("/patient/signup")

            await page.fill("#ps-name", "Test Patient")
            await page.fill("#ps-age", "30")
            await page.select_option("#ps-blood", "O+")
            await page.fill("#ps-phone", "1234567890")
            await page.fill("#ps-email", "test@example.com")
            await page.fill("#ps-pass", "password")
            # Click the button, not the link
            await page.click("button:has-text(\"Create Account\")")

            await page.wait_for_selector("text=MediQueue")
            assert page.url.endswith("/patient/dashboard")
            print("Patient Auth OK.")

            # 3. Test Hospital Discovery
            print("Checking Hospital Discovery...")
            await page.click("button:has-text(\"Find Hospitals Near Me\")")
            await page.wait_for_selector("#disc-btn")
            await page.click("#disc-btn")
            await page.wait_for_selector(".hospital-card")

            cards = await page.query_selector_all(".hospital-card")
            assert len(cards) > 0
            print(f"Found {len(cards)} hospitals near me.")
            print("Hospital Discovery OK.")

            # 4. Test Hospital Auth
            print("Checking Hospital Login...")
            # Use specific button to logout
            await page.click("button:has-text(\"Logout\")")
            # Should be back on landing, let's wait
            await page.wait_for_selector("text=Smart hospital")

            await page.click("button:has-text(\"I'm a Doctor / Hospital Staff\")")
            await page.wait_for_selector("h2:has-text(\"Hospital Portal\")")
            assert page.url.endswith("/hospital/login")

            await page.fill("#hl-name", "Apollo Clinic")
            await page.fill("#hl-user", "DR-123")
            await page.fill("#hl-code", "HOSP-001")
            await page.fill("#hl-pass", "password")
            await page.click("button:has-text(\"Login to Portal\")")

            await page.wait_for_selector("text=Live Queue Management")
            assert page.url.endswith("/hospital/dashboard")
            print("Hospital Auth OK.")

            # 5. Test GPS Cascade Demo
            print("Checking GPS Cascade Demo...")
            await page.fill("#action-id", "MQ-TEST")
            await page.click("button:has-text(\"Trigger GPS Cascade\")")
            await page.wait_for_selector(".cascade-item")

            cascade_items = await page.query_selector_all(".cascade-item")
            assert len(cascade_items) == 3

            names = await page.inner_text("#cascade-result")
            assert "Ravi Kumar" in names
            assert "Sunita Devi" in names
            assert "Arjun Reddy" in names
            print("GPS Cascade Demo OK.")

            print("All verifications passed!")

            # Final screenshot
            await page.screenshot(path="verification_success.png")

            await browser.close()
    finally:
        server_process.terminate()

if __name__ == "__main__":
    asyncio.run(run_verification())
