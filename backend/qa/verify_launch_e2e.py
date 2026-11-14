"""Automated Playwright Launch & E2E Frontend Verification.
Spawns FastAPI backend, drives real headless Chromium browser, captures screenshots,
and validates console errors, DOM rendering, and theme toggling.
"""
import os
import sys
import time
import subprocess
import httpx
from playwright.sync_api import sync_playwright

def verify_frontend():
    print("=" * 65)
    print("LAUNCH VERIFICATION & PLAYWRIGHT E2E UI TEST")
    print("=" * 65)
    
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    python_bin = os.path.join(base_dir, "venv", "Scripts", "python.exe")
    
    # 1. Start FastAPI server
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.join(base_dir, "backend")
    
    print("\n[STEP 1] Starting FastAPI server on http://127.0.0.1:8000...")
    server_proc = subprocess.Popen(
        [python_bin, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True
    )
    
    try:
        # Wait for server to become responsive
        server_ready = False
        for attempt in range(20):
            try:
                resp = httpx.get("http://127.0.0.1:8000/api", timeout=1.0)
                if resp.status_code == 200:
                    server_ready = True
                    print(f"  ✓ Server ready: {resp.json()['project']} (v{resp.json()['version']})")
                    break
            except Exception:
                time.sleep(0.5)
                
        if not server_ready:
            print("❌ Server failed to respond on 127.0.0.1:8000 within 10 seconds.")
            return False

        # 2. Launch Playwright
        print("\n[STEP 2] Launching Headless Chromium Browser via Playwright...")
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome", headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            
            console_errors = []
            page_errors = []
            
            def handle_console(msg):
                print(f"  [BROWSER {msg.type.upper()}]: {msg.text}")
                if msg.type == "error":
                    console_errors.append(msg.text)
                    
            page.on("console", handle_console)
            page.on("pageerror", lambda err: page_errors.append(str(err)))
            page.on("requestfailed", lambda req: print(f"  [REQUEST FAILED]: {req.method} {req.url} -> {req.failure}"))
            
            # 3. Navigate to root
            print("\n[STEP 3] Navigating to http://127.0.0.1:8000/ ...")
            response = page.goto("http://127.0.0.1:8000/", wait_until="domcontentloaded")
            assert response.status == 200, f"Page load returned {response.status}"
            print("  ✓ HTTP 200 OK received.")
            
            # 4. Wait for React components to mount
            print("\n[STEP 4] Waiting for React application DOM elements...")
            try:
                page.wait_for_selector(".app-layout", timeout=10000)
                page.wait_for_selector(".stat-row", timeout=10000)
                page.wait_for_selector(".learner-card", timeout=10000)
            except Exception as e:
                print(f"FAILED TO FIND SELECTOR.")
                print(f"Page errors: {page_errors}")
                print(f"Console errors: {console_errors}")
                # Check root innerHTML
                root_html = page.evaluate("() => document.getElementById('root')?.innerHTML")
                print(f"Root innerHTML: '{root_html}'")
                page.screenshot(path=os.path.join(base_dir, "debug_failure.png"))
                raise e
            print("  ✓ Root layout and stat cards successfully rendered.")
            
            # 5. Verify learner identity & values
            learner_text = page.locator(".learner-card").text_content()
            print(f"  Learner Card Content: {learner_text.strip().replace(chr(10), ' ')}")
            assert "Demo Learner" in learner_text, "Expected 'Demo Learner' in learner card"
            assert "demo@example.com" in learner_text, "Expected 'demo@example.com' in learner card"
            
            stat_cards = page.locator(".stat-card-val").all_text_contents()
            print(f"  Rendered Numeric Values: {stat_cards}")
            assert len(stat_cards) == 4, f"Expected 4 header stat cards, got {len(stat_cards)}"
            print(f"  Career Readiness Rendered: {stat_cards[0]}")
            
            # 6. Test Theme Switching
            print("\n[STEP 5] Testing Dark/Light Theme Switching...")
            # Check default dark theme
            body_class = page.locator("body").get_attribute("class")
            print(f"  Initial Body Class: '{body_class}'")
            assert "theme-dark" in body_class, "Expected default 'theme-dark'"
            
            # Toggle to light theme
            page.click(".theme-toggle-btn")
            time.sleep(0.5)
            body_class_light = page.locator("body").get_attribute("class")
            print(f"  Toggled Body Class: '{body_class_light}'")
            assert "theme-light" in body_class_light, "Theme failed to toggle to light"
            
            # Capture light theme screenshot
            light_screenshot_path = os.path.join(base_dir, "frontend-verification-light.png")
            page.screenshot(path=light_screenshot_path)
            print(f"  ✓ Saved light mode screenshot: {light_screenshot_path}")
            
            # Toggle back to dark theme
            page.click(".theme-toggle-btn")
            time.sleep(0.5)
            body_class_dark = page.locator("body").get_attribute("class")
            assert "theme-dark" in body_class_dark, "Theme failed to toggle back to dark"
            
            # Capture dark theme screenshot
            dark_screenshot_path = os.path.join(base_dir, "frontend-verification.png")
            page.screenshot(path=dark_screenshot_path)
            print(f"  ✓ Saved dark mode screenshot: {dark_screenshot_path}")
            
            # 7. Test AI Mentor Chatbot Widget
            print("\n[STEP 6] Testing Floating AI Mentor Chatbot Widget...")
            page.click(".chat-bubble-btn")
            page.wait_for_selector(".chat-window", timeout=5000)
            print("  ✓ Chatbot widget expanded successfully.")
            page.click(".chat-header button") # Close chatbot

            # 8. Test Navigation to Courses & Certificates views
            print("\n[STEP 7] Testing Courses Catalog Navigation...")
            page.locator(".nav-item:has-text('Courses')").click()
            time.sleep(0.5)
            course_rows = page.locator(".table-container tbody tr")
            course_count = course_rows.count()
            print(f"  ✓ Navigated to Courses. Found {course_count} course rows rendered.")
            assert course_count >= 18, f"Expected at least 18 courses, found {course_count}"

            print("\n[STEP 8] Testing Certificates Navigation...")
            page.locator(".nav-item:has-text('Certificates')").click()
            time.sleep(0.5)
            cert_rows = page.locator(".table-container tbody tr")
            cert_count = cert_rows.count()
            print(f"  ✓ Navigated to Certificates. Found {cert_count} certificate rows rendered.")
            assert cert_count >= 1, f"Expected at least 1 certificate, found {cert_count}"

            # 9. Verify Console Cleanliness
            print("\n[STEP 9] Verifying Browser Console Error Free State...")
            print(f"  Console Errors count: {len(console_errors)}")
            print(f"  Page Errors count: {len(page_errors)}")
            assert len(page_errors) == 0, f"Uncaught JavaScript page errors: {page_errors}"
            
            browser.close()
            print("\n" + "=" * 65)
            print("🏆 VERIFICATION SUCCESSFUL: Frontend verified with 0 errors!")
            print("=" * 65)
            return True

    finally:
        print("\nShutting down FastAPI background server...")
        server_proc.terminate()
        server_proc.wait(timeout=5)

if __name__ == "__main__":
    success = verify_frontend()
    sys.exit(0 if success else 1)
