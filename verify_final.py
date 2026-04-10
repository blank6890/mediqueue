import asyncio
import os
from playwright.async_api import async_playwright

async def verify():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            geolocation={'latitude': 17.3850, 'longitude': 78.4867},
            permissions=['geolocation']
        )
        page = await context.new_page()

        # Start screen
        await page.goto('http://localhost:8000/')
        await page.wait_for_selector('text=I\'m a Patient')
        await page.screenshot(path='/home/jules/verification/final_landing.png')
        print("Captured landing page.")

        # Patient Signup fields
        await page.click('text=I\'m a Patient')
        await page.click('text=Create account')
        await page.wait_for_selector('#ps-name')
        await page.screenshot(path='/home/jules/verification/final_patient_signup.png')
        print("Captured patient signup fields.")

        # Hospital Login fields
        await page.goto('http://localhost:8000/hospital/login')
        await page.wait_for_selector('#hl-code')
        await page.screenshot(path='/home/jules/verification/final_hospital_login.png')
        print("Captured hospital login fields.")

        # Try Demo & Discovery
        await page.goto('http://localhost:8000/')
        await page.click('button:has-text("Try Demo")')

        # Ensure the patient view is visible
        await page.wait_for_selector('#view-patient.active')
        # Ensure screen 4 is active
        await page.wait_for_selector('#screen-4.active')

        await page.screenshot(path='/home/jules/verification/final_patient_dash.png')
        print("Captured patient dashboard.")

        # Click the button specifically in screen-4
        await page.click('#screen-4 button:has-text("Find Hospitals Near Me")')
        await page.wait_for_selector('#screen-5.active')
        await page.click('#disc-btn')
        await page.wait_for_selector('.hospital-card')
        await page.screenshot(path='/home/jules/verification/final_discovery_results.png')
        print("Captured discovery results.")

        # Hospital Dashboard & GPS Cascade
        await page.click('#pill-hospital')
        await page.wait_for_selector('text=Trigger GPS Cascade')
        await page.fill('#action-id', 'MQ-2847')
        await page.click('text=Trigger GPS Cascade')
        await page.wait_for_selector('.cascade-item')
        await page.screenshot(path='/home/jules/verification/final_gps_cascade.png')
        print("Captured GPS cascade results.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(verify())
