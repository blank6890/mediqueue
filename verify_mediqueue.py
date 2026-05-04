import asyncio
from playwright.async_api import async_playwright
import time
import subprocess
import os

async def run_verification():
    # Start server
    server_process = subprocess.Popen(['python', 'app.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(3) # Wait for server to start

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()

            # Mock Geolocation for Hyderabad
            context = await browser.new_context(
                permissions=['geolocation'],
                geolocation={'latitude': 17.3850, 'longitude': 78.4867}
            )
            page = await context.new_page()

            # 1. Landing Page
            print("Capturing Landing Page...")
            await page.goto('http://127.0.0.1:5000/')
            await page.wait_for_selector('.hero-h1')
            await page.screenshot(path='/home/jules/verification/landing_page_v3.png', full_page=True)

            # 2. Try Demo -> Patient Dashboard
            print("Testing Try Demo...")
            await page.click('button:has-text("Try Demo")')
            await page.wait_for_selector('#view-patient.active')
            await page.wait_for_selector('#screen-4.active')
            await page.screenshot(path='/home/jules/verification/patient_dashboard_demo_v3.png', full_page=True)

            # 3. Discovery Flow
            print("Testing Discovery...")
            # Click the visible button
            await page.click('#screen-4 button:has-text("Find Hospitals Near Me")')
            await page.wait_for_selector('#screen-5.active')
            await page.click('#disc-btn')
            # Wait for list to update from "Click below..." to hospital cards
            await page.wait_for_selector('.hospital-card')
            await page.screenshot(path='/home/jules/verification/patient_discovery_v3.png')

            # 4. Hospital Dashboard
            print("Testing Hospital Dashboard...")
            await page.click('#pill-hospital')
            await page.wait_for_selector('#view-hospital.active')
            # Set a demo action ID to trigger cascade
            await page.fill('#action-id', 'MQ-2847')
            await page.click('button:has-text("Trigger GPS Cascade")')
            await page.wait_for_selector('.cascade-item')
            await page.screenshot(path='/home/jules/verification/hospital_dashboard_cascade_v3.png', full_page=True)

            print("Verification screenshots saved to /home/jules/verification/")
            await browser.close()
    finally:
        server_process.terminate()

if __name__ == "__main__":
    os.makedirs('/home/jules/verification', exist_ok=True)
    asyncio.run(run_verification())
