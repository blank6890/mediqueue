import subprocess
import time
import sys
import random
from playwright.sync_api import sync_playwright

def run_tests():
    # Start the Flask app
    print("Starting Flask application...")
    server_process = subprocess.Popen(
        [sys.executable, "app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for the server to spin up
    time.sleep(3)

    url = "http://127.0.0.1:5000"

    try:
        with sync_playwright() as p:
            print("Launching Chromium browser...")
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()

            # Set up geolocation mock permissions and coordinates
            context.grant_permissions(["geolocation"])
            context.set_geolocation({"latitude": 17.3850, "longitude": 78.4867})

            page = context.new_page()

            # --- Test 1: Landing Page ---
            print("Navigating to landing page...")
            page.goto(url)

            # Verify Title/Header
            header_text = page.locator(".hero-h1").inner_text()
            print(f"Hero Header text: {header_text}")
            assert "Smart hospital" in header_text or "MediQueue" in page.title()

            # Check footer badge
            footer_text = page.locator("footer .proto-badge").inner_text()
            print(f"Footer text: {footer_text}")
            assert "Prototype — built for Startup Aid 2026" in footer_text

            # --- Test 2: Try Demo Action ---
            print("Clicking 'Try Demo'...")
            page.click("text=Try Demo")
            time.sleep(1)

            # Verify redirected to Patient Live Queue screen (Screen 4)
            assert page.locator("#screen-4").is_visible()
            live_pos = page.locator("#live-pos").inner_text()
            print(f"Demo Live Position: {live_pos}")
            assert live_pos == "3"

            # Clear localStorage so we can test login flows
            print("Clearing localStorage...")
            page.evaluate("localStorage.clear()")
            page.goto(url)
            time.sleep(1)

            # --- Test 3: Patient Portal Navigation ---
            print("Navigating to Patient Login...")
            page.click("#view-landing button:has-text(\"I'm a Patient\")")
            time.sleep(1)
            assert page.locator("#view-patient-login").is_visible()

            # Go to signup
            print("Navigating to Patient Signup...")
            page.click("#view-patient-login a:has-text('Create account')")
            time.sleep(1)
            assert page.locator("#view-patient-signup").is_visible()

            # Go back to login
            print("Clicking back to login...")
            page.click("#view-patient-signup .back-link")
            time.sleep(1)
            assert page.locator("#view-patient-login").is_visible()

            # Go back to home
            print("Clicking back to home...")
            page.click("#view-patient-login .back-link")
            time.sleep(1)
            assert page.locator("#view-landing").is_visible()

            # --- Test 4: Doctor / Hospital Portal Navigation ---
            print("Navigating to Hospital Login...")
            page.click("#view-landing button:has-text(\"I'm a Doctor / Hospital Staff\")")
            time.sleep(1)
            assert page.locator("#view-hospital-login").is_visible()

            # Go back to home
            print("Clicking back to home from hospital login...")
            page.click("#view-hospital-login .back-link")
            time.sleep(1)
            assert page.locator("#view-landing").is_visible()

            # --- Test 5: Patient Signup & Login flow ---
            print("Testing Patient Signup...")
            page.click("#view-landing button:has-text(\"I'm a Patient\")")
            time.sleep(1)
            page.click("#view-patient-login a:has-text('Create account')")
            time.sleep(1)

            # Fill out the signup fields
            rand_suffix = str(random.randint(1000, 9999))
            phone_num = "9" + rand_suffix + "12345"
            email_addr = f"patient_{rand_suffix}@example.com"

            page.fill("#ps-name", "Test Patient")
            page.fill("#ps-age", "30")
            page.select_option("#ps-blood", "O+")
            page.fill("#ps-cond", "Asthma")
            page.fill("#ps-phone", phone_num)
            page.fill("#ps-email", email_addr)
            page.fill("#ps-pass", "secret123")

            page.click("#view-patient-signup button:has-text('Create Account')")
            time.sleep(2)

            # After signup, the user is logged in automatically.
            assert page.locator("#view-patient").is_visible()
            print("Patient Signup & auto-login succeeded!")

            # Check profile data
            name_val = page.locator("#profile-name").inner_text()
            phone_val = page.locator("#profile-phone").inner_text()
            print(f"Profile: Name={name_val}, Phone={phone_val}")
            assert name_val == "Test Patient"
            assert phone_val == phone_num

            # --- Test 6: Hospital Discovery Feature ---
            print("Navigating to Discovery Screen...")
            page.click("#screen-4 button:has-text('Find Hospitals Near Me')")
            time.sleep(1)
            assert page.locator("#screen-5").is_visible()

            # Perform Nearby Search
            print("Searching nearby hospitals...")
            page.click("#disc-btn")
            time.sleep(2)

            # Check hospital cards are rendered
            hospital_cards = page.locator(".hospital-card")
            card_count = hospital_cards.count()
            print(f"Found {card_count} hospital cards near Hyderabad GPS.")
            assert card_count > 0

            # Check first hospital details
            first_h_name = hospital_cards.first.locator(".h-name").inner_text()
            first_h_dist = hospital_cards.first.locator(".h-dist").inner_text()
            print(f"Nearest hospital: {first_h_name} at distance: {first_h_dist}")

            # Click "Book Here"
            print("Clicking 'Book Here' on nearest hospital...")
            hospital_cards.first.locator("button:has-text('Book Here')").click()
            time.sleep(1)

            # Verify we are on screen 2 and hospital dropdown matches
            assert page.locator("#screen-2").is_visible()
            selected_h_val = page.locator("#b-hospital").evaluate("el => el.value")
            print(f"Pre-filled Hospital select value: {selected_h_val}")
            assert selected_h_val == first_h_name

            # Verify that Doctor, Department, and Time Slot are dynamically populated and not empty!
            doctor_options = page.locator("#b-doctor option")
            dept_options = page.locator("#b-dept option")
            time_options = page.locator("#b-time option")
            assert doctor_options.count() > 0
            assert dept_options.count() > 0
            assert time_options.count() > 0
            print(f"Successfully verified dynamic populate: {doctor_options.count()} docs, {dept_options.count()} depts, {time_options.count()} slots.")

            # --- Test 7: Booking a Slot ---
            print("Booking slot...")
            page.click("#book-btn")
            time.sleep(2)

            # Verify screen 3 (QR screen) is visible
            assert page.locator("#screen-3").is_visible()
            booking_id = page.locator("#c-id").inner_text()
            print(f"Booking confirmed! Booking ID: {booking_id}")
            assert "MQ-" in booking_id

            # --- Test 8: Hospital Dashboard ---
            # Let's log out first
            print("Logging out patient...")
            page.click("#main-nav button:has-text('Logout')")
            time.sleep(1)
            assert page.locator("#view-landing").is_visible()

            # Log in as a doctor/hospital
            print("Navigating to Hospital Portal Login...")
            page.click("#view-landing button:has-text(\"I'm a Doctor / Hospital Staff\")")
            time.sleep(1)

            # Doctor IDs must be unique or random to prevent 401 error if user already exists with other password in prototype DB
            doctor_id = f"DR-Ramesh-{rand_suffix}"
            page.fill("#hl-name", "Apollo Clinic — Jubilee Hills")
            page.fill("#hl-user", doctor_id)
            page.fill("#hl-code", "HOSP-001")
            page.fill("#hl-pass", "hospPass123")

            page.click("#view-hospital-login button:has-text('Login to Portal')")
            time.sleep(2)

            # Verify Hospital Dashboard is visible
            assert page.locator("#view-hospital").is_visible()
            dash_title = page.locator("#dash-h-name").inner_text()
            print(f"Hospital Dashboard loaded: {dash_title}")
            assert "Apollo Clinic — Jubilee Hills" in dash_title

            # Verify total/booked count
            total_val = page.locator("#kpi-total").inner_text()
            print(f"Total in queue KPI: {total_val}")

            # Test Quick Action - Mark as Present
            print("Testing Mark as Present action...")
            page.fill("#action-id", booking_id)
            page.click("text=Mark as Present")
            time.sleep(2)

            # Verify action message shows success
            action_msg = page.locator("#action-msg").inner_text()
            print(f"Action message: {action_msg}")
            assert "updated to present" in action_msg.lower() or "success" in action_msg.lower()

            # Test GPS Cascade action
            print("Testing GPS Cascade action...")
            page.fill("#action-id", booking_id)
            page.click("text=Trigger GPS Cascade")
            time.sleep(2)

            # Check GPS Cascade panel is populated with demo results
            cascade_items = page.locator(".cascade-item")
            assert cascade_items.count() == 3
            print("GPS Cascade items successfully populated!")

            # Verify status badges on cascade items
            badge_1 = cascade_items.nth(0).locator(".badge-demo").inner_text().strip().upper()
            badge_2 = cascade_items.nth(1).locator(".badge-demo").inner_text().strip().upper()
            badge_3 = cascade_items.nth(2).locator(".badge-demo").inner_text().strip().upper()
            print(f"Cascade Badges: 1={badge_1}, 2={badge_2}, 3={badge_3}")
            assert badge_1 == "NOTIFIED"
            assert badge_2 == "PENDING"
            assert badge_3 == "STANDBY"

            print("All MediQueue tests passed with 100% success!")

    except Exception as e:
        print(f"ERROR: Tests failed: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        print("Terminating Flask application server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
        print("Done!")

if __name__ == "__main__":
    run_tests()
