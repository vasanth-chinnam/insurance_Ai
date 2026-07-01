import os
import time
import asyncio
from playwright.async_api import async_playwright

ARTIFACTS_DIR = "C:/Users/vasanth/.gemini/antigravity-ide/brain/906544eb-4b13-4b39-ab87-88670dddecaf"

async def run_systematic_ui_tests():
    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 800})
        
        print("Navigating to frontend...")
        await page.goto("http://localhost:5173/")
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(1000)
        
        # Bypass login screen
        await page.evaluate("""() => {
          localStorage.setItem("insureai_token", "mock-google-token-U12345");
          localStorage.setItem("insureai_user", JSON.stringify({
            name: "Vasanth Chinnam",
            email: "vasanth@example.com",
            role: "user",
            avatar: ""
          }));
          window.location.reload();
        }""")
        await page.wait_for_timeout(2000)
        
        # Helper to click left nav items
        async def go_to_tab(label_text):
            print(f"Switching to tab: {label_text}")
            await page.click(f"aside.sidebar nav.sidebar-nav div.nav-item:has-text('{label_text}')")
            await page.wait_for_timeout(1500)

        # ── TAB 1: Policy Q&A ──────────────────────────────────────────────────
        await go_to_tab("Policy Q&A")
        # Query Motor policy Q&A
        await page.click("button:has-text('🚗')")
        await page.wait_for_timeout(500)
        await page.fill(".input-wrapper input[type='text']", "What is the deductible for collision coverage?")
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(4000)
        await page.screenshot(path=os.path.join(ARTIFACTS_DIR, "ui_policy_qa_motor.png"))

        # Query Health policy Q&A
        await page.click("button:has-text('🏥')")
        await page.wait_for_timeout(500)
        await page.fill(".input-wrapper input[type='text']", "Is surgery covered?")
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(4000)
        await page.screenshot(path=os.path.join(ARTIFACTS_DIR, "ui_policy_qa_health.png"))

        # ── TAB 2: Claim Estimator ─────────────────────────────────────────────
        await go_to_tab("Claim Estimator")
        
        # Test Motor Claim Estimator
        await page.click("button:has-text('🚗')")
        await page.wait_for_timeout(500)
        await page.fill("[name='claimant_name']", "Vasanth")
        await page.fill("[name='vehicle_number']", "TN-07-CS-2026")
        await page.fill("[name='vehicle_make']", "Honda")
        await page.fill("[name='vehicle_model']", "Shine")
        await page.fill("[name='year']", "2020")
        await page.fill("[name='incident_date']", "2026-06-30")
        await page.fill("[name='incident_description']", "Minor front scratch bumper damage")
        await page.fill("[name='policy_number']", "DG-MOTOR-2025-042")

        # Create a valid 1x1 PNG image to bypass frontend type check
        import base64
        temp_img = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scratch", "temp_motor.png")
        os.makedirs(os.path.dirname(temp_img), exist_ok=True)
        with open(temp_img, "wb") as f:
            f.write(base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="))

        file_input = page.locator("input[type='file']")
        await file_input.set_input_files(temp_img)
        await page.wait_for_timeout(2000)
        await page.click("text=Submit Claim Request")
        await page.wait_for_timeout(6000)
        await page.screenshot(path=os.path.join(ARTIFACTS_DIR, "ui_claims_estimator_motor.png"))

        # Test Health Claim Estimator
        await page.click("button:has-text('🏥')")
        await page.wait_for_timeout(500)
        await page.fill("input[placeholder*='HL-2025-001']", "HL-2025-042")
        await page.fill("label:has-text('CLAIMANT NAME') + input", "Vasanth")
        await page.fill("label:has-text('PATIENT NAME') + input", "Vasanth Patient")
        await page.fill("label:has-text('DIAGNOSIS') + input", "Viral fever check")
        await page.fill("label:has-text('TOTAL BILL AMOUNT') + input", "15000")
        await page.fill("label:has-text('SUM INSURED') + input", "100000")
        await page.click("text=Submit Claim Request")
        await page.wait_for_timeout(6000)
        await page.screenshot(path=os.path.join(ARTIFACTS_DIR, "ui_claims_estimator_health.png"))

        # Test Travel Claim Estimator
        await page.click("button:has-text('✈️')")
        await page.wait_for_timeout(500)
        await page.fill("input[placeholder*='TR-2025-001']", "TV-2025-042")
        await page.fill("label:has-text('CLAIMANT NAME') + input", "Vasanth")
        await page.fill("label:has-text('DELAY HOURS') + input", "6")
        await page.fill("label:has-text('SUM INSURED') + input", "50000")
        await page.fill("label:has-text('DESCRIPTION') + textarea", "Flight delayed at terminal")
        await page.click("text=Submit Claim Request")
        await page.wait_for_timeout(6000)
        await page.screenshot(path=os.path.join(ARTIFACTS_DIR, "ui_claims_estimator_travel.png"))

        # ── TAB 3: Fraud Detection ─────────────────────────────────────────────
        await go_to_tab("Fraud Detection")
        await page.click("button:has-text('🚗')")
        await page.wait_for_timeout(500)
        await page.fill("label:has-text('POLICY NUMBER') + input", "DG-MOTOR-2025-042")
        await page.fill("label:has-text('CLAIM AMOUNT') + input", "60000")
        await page.fill("label:has-text('DAYS AFTER INCIDENT') + input", "2")
        await page.fill("label:has-text('PREVIOUS CLAIMS') + input", "3")
        await page.fill("label:has-text('DESCRIPTION') + textarea", "Front bumper dent details")
        await page.click("text=Analyze for Fraud")
        await page.wait_for_timeout(4000)
        await page.screenshot(path=os.path.join(ARTIFACTS_DIR, "ui_fraud_detection_motor.png"))

        # ── TAB 4: Risk Profiler ───────────────────────────────────────────────
        await go_to_tab("Risk Profiler")
        await page.click("button:has-text('🚗')")
        await page.wait_for_timeout(500)
        await page.fill("label:has-text('DRIVER AGE') + input", "28")
        await page.fill("label:has-text('VEHICLE AGE (YEARS)') + input", "2")
        await page.fill("label:has-text('ANNUAL KM DRIVEN') + input", "15000")
        await page.click("text=Generate Risk Profile")
        await page.wait_for_timeout(4000)
        await page.screenshot(path=os.path.join(ARTIFACTS_DIR, "ui_risk_profiler_motor.png"))

        # ── TAB 5: Crop Insurance ─────────────────────────────────────────────
        await go_to_tab("Crop Insurance")
        await page.select_option("select", value="F001")
        await page.click("text=Run Crop Agent")
        await page.wait_for_timeout(6000)
        await page.screenshot(path=os.path.join(ARTIFACTS_DIR, "ui_crop_insurance_ramesh.png"))

        # ── TAB 6: Renewal Compare ─────────────────────────────────────────────
        await go_to_tab("Renewal Compare")
        await page.click("button:has-text('🚗')")
        await page.wait_for_timeout(500)
        await page.fill("label:has-text('USER NAME') + input", "Vasanth Kumar")
        await page.fill("label:has-text('USER AGE') + input", "30")
        await page.fill("label:has-text('USER CITY') + input", "Hyderabad")
        await page.fill("label:has-text('PROVIDER NAME') + input", "Current Insurer")
        await page.fill("label:has-text('ANNUAL PREMIUM') + input", "12000")
        await page.fill("label:has-text('SUM INSURED') + input", "500000")
        await page.click("text=Find Best Deal")
        await page.wait_for_timeout(6000)
        await page.screenshot(path=os.path.join(ARTIFACTS_DIR, "ui_renewal_compare_motor.png"))

        # ── TAB 7: Agent Automation ────────────────────────────────────────────
        await go_to_tab("Agent Automation")
        await page.fill("textarea[placeholder*='Describe your insurance situation']", "My car got damaged, policy DG-MOTOR-2025-042, estimating ₹15,000 repair cost.")
        await page.click("text=Run AI")
        await page.wait_for_timeout(8000)
        await page.screenshot(path=os.path.join(ARTIFACTS_DIR, "ui_agent_automation_claims.png"))

        print("All tabs tested successfully!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_systematic_ui_tests())
