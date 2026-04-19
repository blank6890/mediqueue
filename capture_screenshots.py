import asyncio
from playwright.async_api import async_playwright
import os
import subprocess
import time

async def capture():
    # Start Flask server
    proc = subprocess.Popen(["python3", "app.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(5)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Landing
        await page.goto("http://localhost:5000")
        await page.wait_for_timeout(2000)
        await page.screenshot(path="landing.png")

        # Try Demo -> Patient Dashboard
        await page.click("button:has-text('Try Demo')")
        await page.wait_for_timeout(2000)
        await page.screenshot(path="patient_dashboard.png")

        # Discovery
        await page.click("button:has-text('Find Hospitals Near Me')")
        await page.wait_for_timeout(2000)
        await page.screenshot(path="discovery.png")

        # Hospital Dashboard
        await page.goto("http://localhost:5000")
        await page.wait_for_timeout(2000)
        await page.click("button:has-text('I\'m a Doctor / Hospital Staff')")
        await page.fill("input[placeholder='Hospital Name']", "Apollo Clinic")
        await page.fill("input[placeholder='Doctor ID or Email']", "DOC-001")
        # Find input by placeholder containing HOSP
        await page.locator("input[placeholder*='HOSP']").fill("HOSP-001")
        await page.fill("input[placeholder='Password']", "password")
        await page.click("button:has-text('Login')")
        await page.wait_for_timeout(2000)
        await page.click("button:has-text('Trigger GPS Cascade')")
        await page.wait_for_timeout(2000)
        await page.screenshot(path="hospital_dashboard.png")

        await browser.close()

    proc.terminate()

if __name__ == "__main__":
    asyncio.run(capture())
