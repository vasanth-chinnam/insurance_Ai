import os
import time
import asyncio
from playwright.async_api import async_playwright

ARTIFACTS_DIR = "C:/Users/vasanth/.gemini/antigravity-ide/brain/906544eb-4b13-4b39-ab87-88670dddecaf"

async def run_auth_verification():
    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 800})
        
        # Listen for console messages
        page.on("console", lambda msg: print(f"BROWSER CONSOLE: {msg.text}"))

        try:
            print("Navigating to login page...")
            await page.goto("http://localhost:5173/")
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(2000)
            
            # 1. Capture Login Screen
            await page.screenshot(path=os.path.join(ARTIFACTS_DIR, "auth_login_screen.png"))
            print("Captured Login Page screenshot")

            # 2. Switch to Register Page
            print("Switching to Register Page...")
            await page.click("text=Register Now")
            await page.wait_for_timeout(1000)
            await page.screenshot(path=os.path.join(ARTIFACTS_DIR, "auth_register_screen.png"))
            print("Captured Register Page screenshot")

            # 3. Fill Register Form
            print("Filing Register Form...")
            await page.fill("label:has-text('Full Name') + input", "Vasanth Chinnam")
            test_email = f"vasanth.test{int(time.time())}@example.com"
            await page.fill("label:has-text('Email') + input", test_email)
            await page.fill("label:has-text('Phone') + input", "9876543210")
            # Password
            await page.fill("input[placeholder*='Min 8 characters']", "password123")
            await page.fill("label:has-text('Confirm Password') + input", "password123")
            await page.screenshot(path=os.path.join(ARTIFACTS_DIR, "auth_register_filled.png"))
            
            # Click Create Account
            print("Clicking Create Account...")
            await page.click("button:has-text('Create Account')")
            
            # Wait for dashboard to load and redirect to finish
            print("Waiting for logout button to appear...")
            await page.wait_for_selector("button[title='Log out']", timeout=10000)
            await page.screenshot(path=os.path.join(ARTIFACTS_DIR, "auth_dashboard_logged_in.png"))
            print("Successfully registered and logged in!")

            # 4. Test Logout
            print("Clicking Logout...")
            await page.click("button[title='Log out']")
            await page.wait_for_timeout(2000)
            # Switch to Login page if we ended up on Register page
            if await page.locator("text=Already have an account?").count() > 0:
                print("Switching back to Login Page...")
                await page.click("text=Log in")
                await page.wait_for_timeout(1000)
            await page.screenshot(path=os.path.join(ARTIFACTS_DIR, "auth_logged_out.png"))
            print("Successfully logged out!")

            # 5. Test Google Login
            print("Triggering mock Google login callback...")
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
            await page.wait_for_selector("button[title='Log out']", timeout=10000)
            await page.screenshot(path=os.path.join(ARTIFACTS_DIR, "auth_google_logged_in.png"))
            print("Successfully logged in via Google!")

        except Exception as e:
            print(f"Error occurred: {e}")
            await page.screenshot(path=os.path.join(ARTIFACTS_DIR, "auth_error.png"))
            print("Saved auth_error.png screenshot")
            raise e
        finally:
            await browser.close()
            print("Browser closed.")

if __name__ == "__main__":
    asyncio.run(run_auth_verification())
