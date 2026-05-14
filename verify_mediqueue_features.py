from playwright.sync_api import sync_playwright
import time
import os

def run_verification(page):
    # 1. Landing Page CTAs
    print("Testing Landing Page...")
    page.goto("http://localhost:5000")
    page.wait_for_timeout(1000)
    page.screenshot(path="/home/jules/verification/screenshots/landing.png")

    # 2. Try Demo
    print("Testing Try Demo...")
    page.get_by_text("Try Demo").click()
    page.wait_for_timeout(1000)
    page.screenshot(path="/home/jules/verification/screenshots/demo_patient.png")

    # 3. Logout
    print("Testing Logout...")
    page.get_by_text("Logout").click()
    page.wait_for_timeout(1000)

    # 4. Patient Signup
    print("Testing Patient Signup...")
    page.get_by_role("button", name="I'm a Patient").click()
    page.wait_for_timeout(500)
    page.get_by_role("link", name="Create account").click()
    page.wait_for_timeout(500)

    unique_phone = str(int(time.time()))[-10:]
    page.fill("#ps-name", "Test Patient")
    page.fill("#ps-age", "35")
    page.select_option("#ps-blood", "O+")
    page.fill("#ps-cond", "None")
    page.fill("#ps-phone", unique_phone)
    page.fill("#ps-email", f"test_{unique_phone}@example.com")
    page.fill("#ps-pass", "password123")
    page.screenshot(path="/home/jules/verification/screenshots/patient_signup_form.png")
    page.get_by_role("button", name="Create Account").click()
    page.wait_for_timeout(2000)
    page.screenshot(path="/home/jules/verification/screenshots/patient_dashboard.png")

    # 5. Hospital Discovery
    print("Testing Hospital Discovery...")
    page.locator("#view-patient-dashboard #screen-1 button:has-text('Find Hospitals Near Me')").click()
    page.wait_for_timeout(500)
    page.get_by_role("button", name="Search Nearby 🔎").click()
    page.wait_for_timeout(2000)
    page.screenshot(path="/home/jules/verification/screenshots/hospital_discovery.png")

    # 6. Booking
    print("Testing Booking...")
    if page.locator(".hospital-card").count() > 0:
        page.locator(".hospital-card").first.click()
        page.wait_for_timeout(500)
    else:
        page.locator("#view-patient-dashboard #screen-1 button:has-text('Book New Slot')").click()

    page.wait_for_timeout(500)
    page.get_by_role("button", name="Confirm Booking →").click()
    page.wait_for_timeout(2000)
    page.screenshot(path="/home/jules/verification/screenshots/booking_confirmed.png")

    # 7. Live Queue
    print("Testing Live Queue...")
    # Using dispatchEvent to click hidden elements if Playwright thinks they're not visible
    page.locator("#view-patient-dashboard #screen-3 .cta").dispatch_event("click")
    page.wait_for_timeout(1000)
    page.screenshot(path="/home/jules/verification/screenshots/live_queue.png")

    # 8. Hospital Login
    print("Testing Hospital Login...")
    page.get_by_text("Logout").click()
    page.wait_for_timeout(500)
    page.get_by_role("button", name="I'm a Doctor / Hospital Staff").click()
    page.wait_for_timeout(500)
    page.fill("#hl-name", "Apollo Clinic")
    page.fill("#hl-user", "doc1")
    page.fill("#hl-code", "HOSP-001")
    page.fill("#hl-pass", "pass")
    page.screenshot(path="/home/jules/verification/screenshots/hospital_login_form.png")
    page.get_by_role("button", name="Login to Portal").click()
    page.wait_for_timeout(2000)
    page.screenshot(path="/home/jules/verification/screenshots/hospital_dashboard.png")

    # 9. GPS Cascade Demo
    print("Testing GPS Cascade Demo...")
    page.get_by_role("button", name="Trigger GPS Cascade").click()
    page.wait_for_timeout(1000)
    page.screenshot(path="/home/jules/verification/screenshots/gps_cascade_demo.png")

    print("Verification complete!")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir="/home/jules/verification/videos",
            permissions=["geolocation"],
            geolocation={"latitude": 17.3850, "longitude": 78.4867}
        )
        page = context.new_page()
        try:
            run_verification(page)
        except Exception as e:
            print(f"Error during verification: {e}")
            page.screenshot(path="/home/jules/verification/screenshots/error.png")
        finally:
            context.close()
            browser.close()
