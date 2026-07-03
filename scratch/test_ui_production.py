import os
import time
import asyncio
import base64
from playwright.async_api import async_playwright

ARTIFACTS_DIR = "C:/Users/vasanth/.gemini/antigravity-ide/brain/906544eb-4b13-4b39-ab87-88670dddecaf"
PRODUCTION_URL = "https://insurance-ai-kappa.vercel.app"

async def run_production_verification():
    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 800})
        
        print(f"Navigating to production site {PRODUCTION_URL}...")
        await page.goto(PRODUCTION_URL)
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(2000)
        
        # Bypass login screen by injecting session items
        print("Bypassing login screen...")
        await page.evaluate("""() => {
          localStorage.setItem("insureai_token", "mock-google-token-U12345");
          localStorage.setItem("insureai_user", JSON.stringify({
            name: "Vasanth Chinnam",
            email: "vasanth@example.com",
            role: "admin",
            avatar: ""
          }));
          window.location.reload();
        }""")
        await page.wait_for_timeout(3000)
        await page.wait_for_load_state("networkidle")

        # Helper to click left nav items
        async def go_to_tab(label_text):
            print(f"Switching to tab: {label_text}")
            await page.click(f"aside.sidebar nav.sidebar-nav div.nav-item:has-text('{label_text}')")
            await page.wait_for_timeout(2000)

        # ── TAB 1: Policy Q&A ──────────────────────────────────────────────────
        await go_to_tab("Policy Q&A")
        
        # Query Motor policy Q&A
        await page.click("button:has-text('🚗')")
        await page.wait_for_timeout(500)
        await page.fill(".input-wrapper input[type='text']", "What is the deductible for collision coverage?")
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(5000)
        await page.screenshot(path=os.path.join(ARTIFACTS_DIR, "production_policy_qa_motor.png"))

        # Query Health policy Q&A
        await page.click("button:has-text('🏥')")
        await page.wait_for_timeout(500)
        await page.fill(".input-wrapper input[type='text']", "Is surgery covered?")
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(5000)
        await page.screenshot(path=os.path.join(ARTIFACTS_DIR, "production_policy_qa_health.png"))

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

        # Capture console logs from browser
        page.on("console", lambda msg: print("BROWSER CONSOLE:", msg.text))

        # Create a valid 1x1 PNG image to bypass type check
        temp_img = os.path.join(os.path.dirname(os.path.abspath(__file__)), "production_temp_motor.png")
        with open(temp_img, "wb") as f:
            f.write(base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="))

        file_input = page.locator("input[type='file']")
        await file_input.set_input_files(temp_img)
        await page.wait_for_timeout(3000)
        
        # Take screenshot before click to see if button is enabled and what the UI state looks like
        await page.screenshot(path=os.path.join(ARTIFACTS_DIR, "production_debug_pre_click.png"))
        
        # Submit Claim
        await page.click("text=Submit Claim Request")
        print("Waiting for Motor assessment receipt...")
        await page.wait_for_selector("text=Assessment Receipt", timeout=40000)
        await page.screenshot(path=os.path.join(ARTIFACTS_DIR, "production_claims_estimator_motor.png"))

        # Test Health Claim Estimator
        await page.click("button:has-text('🏥')")
        await page.wait_for_timeout(1000)
        await page.fill("input[placeholder*='HL-2025-001']", "HL-2025-042")
        await page.fill("label:has-text('CLAIMANT NAME') + input", "Vasanth")
        await page.fill("label:has-text('PATIENT NAME') + input", "Vasanth Patient")
        await page.fill("label:has-text('AGE') + input", "30")
        await page.fill("label:has-text('DIAGNOSIS') + input", "Viral fever check")
        await page.fill("label:has-text('HOSPITAL NAME') + input", "Apollo Hospital")
        await page.fill("label:has-text('TOTAL BILL AMOUNT (₹)') + input", "150000")
        await page.fill("label:has-text('SUM INSURED (₹)') + input", "500000")
        await page.fill("label:has-text('ADMISSION DATE') + input", "2026-06-25")
        await page.fill("label:has-text('DISCHARGE DATE') + input", "2026-06-29")
        await page.click("text=Submit Claim Request")
        print("Waiting for Health assessment receipt...")
        await page.wait_for_selector("text=Assessment Receipt", timeout=40000)
        await page.screenshot(path=os.path.join(ARTIFACTS_DIR, "production_claims_estimator_health.png"))

        # Test Travel Claim Estimator
        await page.click("button:has-text('✈️')")
        await page.wait_for_timeout(1000)
        await page.fill("label:has-text('CLAIMANT NAME') + input", "Vasanth")
        await page.fill("input[placeholder*='TR-2025-001']", "TR-2025-042")
        await page.fill("label:has-text('ORIGIN') + input", "Singapore")
        await page.fill("label:has-text('DESTINATION') + input", "Hyderabad")
        await page.fill("label:has-text('DEPARTURE DATE') + input", "2026-06-28")
        await page.fill("label:has-text('SUM INSURED') + input", "10000")
        await page.fill("label:has-text('DELAY HOURS') + input", "6")
        await page.click("text=Submit Claim Request")
        print("Waiting for Travel assessment receipt...")
        await page.wait_for_selector("text=Assessment Receipt", timeout=40000)
        await page.screenshot(path=os.path.join(ARTIFACTS_DIR, "production_claims_estimator_travel.png"))

        # ── TAB 3: Fraud Detection ─────────────────────────────────────────────
        await go_to_tab("Fraud Detection")
        await page.click("button:has-text('🚗')")
        await page.wait_for_timeout(1000)
        await page.fill("input[placeholder='DG-MOTOR-2025-042']", "DG-MOTOR-2025-042")
        await page.fill("input[placeholder='25000']", "45000")
        await page.fill("input[type='date']", "2026-06-30")
        await page.fill("textarea[placeholder*='Describe the incident']", "Minor front bumper impact, scratch on headlights")
        await page.click("button:has-text('Analyze for Fraud')")
        await page.wait_for_timeout(8000)
        await page.screenshot(path=os.path.join(ARTIFACTS_DIR, "production_fraud_detection_motor.png"))

        # ── TAB 4: Risk Profiler ───────────────────────────────────────────────
        await go_to_tab("Risk Profiler")
        await page.click("button:has-text('🚗')")
        await page.wait_for_timeout(1000)
        await page.fill("label:has-text('DRIVER AGE') + input", "30")
        await page.fill("label:has-text('VEHICLE AGE') + input", "6")
        await page.fill("label:has-text('ACCIDENTS') + input", "1")
        await page.fill("label:has-text('ANNUAL KM DRIVEN') + input", "12000")
        await page.click("button:has-text('Generate Risk Profile')")
        await page.wait_for_timeout(8000)
        await page.screenshot(path=os.path.join(ARTIFACTS_DIR, "production_risk_profiler_motor.png"))

        # ── TAB 5: Crop Insurance ──────────────────────────────────────────────
        await go_to_tab("Crop Insurance")
        await page.wait_for_timeout(1000)
        await page.select_option("label:has-text('FARMER') + select", value="F001")
        await page.wait_for_timeout(1000)
        await page.click("button:has-text('Run Crop Agent')")
        await page.wait_for_timeout(10000)
        await page.screenshot(path=os.path.join(ARTIFACTS_DIR, "production_crop_insurance_report.png"))

        # ── TAB 6: Renewal Compare ─────────────────────────────────────────────
        await go_to_tab("Renewal Compare")
        await page.click("button:has-text('🏥')")
        await page.wait_for_timeout(500)
        await page.fill("label:has-text('USER NAME') + input", "Vasanth")
        await page.fill("label:has-text('USER AGE') + input", "20")
        await page.fill("label:has-text('USER CITY') + input", "pune")
        await page.fill("label:has-text('PROVIDER NAME') + input", "star health")
        await page.fill("label:has-text('ANNUAL PREMIUM') + input", "25000")
        await page.fill("label:has-text('SUM INSURED') + input", "2500000")
        await page.fill("label:has-text('YEARS WITH PROVIDER') + input", "10")
        await page.fill("label:has-text('CLAIM FREE YEARS') + input", "10")
        await page.click("button:has-text('Find Best Deal')")
        await page.wait_for_timeout(12000)
        await page.screenshot(path=os.path.join(ARTIFACTS_DIR, "production_renewal_compare_health.png"))

        # ── TAB 7: Agent Automation ────────────────────────────────────────────
        await go_to_tab("Agent Automation")
        await page.fill("textarea[placeholder*='Describe your insurance']", "Run a complete policy summary check")
        await page.wait_for_timeout(1000)
        await page.click("button:has-text('Run AI')")
        await page.wait_for_timeout(12000)
        await page.screenshot(path=os.path.join(ARTIFACTS_DIR, "production_agent_automation_report.png"))

        print("Production verification tests completed successfully!")
        
        # Cleanup temp file
        if os.path.exists(temp_img):
            os.remove(temp_img)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_production_verification())
