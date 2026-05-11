import asyncio
from playwright.async_api import async_playwright
import os
import time

async def verify():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            permissions=["geolocation"],
            geolocation={"latitude": 17.4447, "longitude": 78.3483},
        )
        page = await context.new_page()

        try:
            # 1. Landing Page
            print("Going to http://localhost:5000")
            await page.goto("http://localhost:5000")
            await page.wait_for_load_state("networkidle")

            # Wait for any text that should be there
            await page.wait_for_selector("text=Smart hospital", state="visible", timeout=5000)
            await page.screenshot(path="verification/landing_v3.png")
            print("Landing page verified")

            # 2. Try Demo
            await page.click("button:has-text('Try Demo')")
            # The screen title is "Live Queue"
            await page.wait_for_selector("h2:has-text('Live Queue')", state="visible", timeout=5000)
            await page.screenshot(path="verification/demo_dashboard_v3.png")
            print("Demo dashboard verified")

            # 3. Find Hospitals Near Me
            await page.click("button:has-text('Find Hospitals Near Me')")
            # Screen 5 title: "Find Nearby"
            await page.wait_for_selector("h2:has-text('Find Nearby')", state="visible", timeout=5000)

            # Trigger search
            await page.click("button:has-text('Search Nearby')")

            # Wait for results (km)
            await page.wait_for_selector("text=km", state="visible", timeout=10000)
            await page.screenshot(path="verification/discovery_v3.png")
            print("Discovery page verified")

            # 4. Hospital Dashboard Demo
            await page.goto("http://localhost:5000/hospital/login")
            await page.wait_for_selector("h2:has-text('Hospital Portal')", state="visible", timeout=5000)
            await page.fill("input[placeholder='Hospital Code (e.g. HOSP-001)']", "HOSP-001")
            await page.fill("input[placeholder='Doctor ID or Email']", "dr.ramesh@apollo.com")
            await page.fill("input[placeholder='Password']", "password123")
            await page.click("button:has-text('Login')")

            await page.wait_for_selector("text=Hospital Dashboard", state="visible", timeout=5000)
            await page.screenshot(path="verification/hospital_dashboard_v3.png")
            print("Hospital dashboard verified")

            # 5. GPS Cascade Demo
            await page.click("button:has-text('Trigger GPS Cascade')")
            await page.wait_for_selector("text=Ravi Kumar", state="visible", timeout=5000)
            await page.screenshot(path="verification/cascade_demo_v3.png")
            print("Cascade demo verified")

        except Exception as e:
            print(f"Error during verification: {e}")
            await page.screenshot(path="verification/error_debug_v3.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(verify())
