import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    os.makedirs('test_screenshots', exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        
        print("Navigating to dashboard...")
        await page.goto("http://localhost:5173")
        
        # Wait for login screen and click demo login button
        # Based on typical UI, there might be a button with text 'Demo' or 'Sign In'
        try:
            # We look for a button containing "Demo" or just click the first button
            demo_btn = page.locator("button", has_text="Demo")
            if await demo_btn.count() > 0:
                await demo_btn.first.click()
            else:
                await page.locator("button").first.click()
        except Exception as e:
            print("Login click failed or already logged in:", e)
            
        print("Waiting for dashboard to render...")
        await page.wait_for_timeout(3000)
        
        # 1. Main Dashboard Screenshot (TC-18: Alert escalation view, TC-09: Simulated fraud visible)
        print("Taking dashboard main screenshot...")
        await page.screenshot(path="test_screenshots/tc18_dashboard_main.png")
        
        # 2. Open an alert to see SHAP chart
        print("Opening alert modal...")
        # Click on the first alert row in the feed
        alert_rows = page.locator(".alerts-feed li, .alert-item, .alert-row, tr").filter(has_text="HIGH")
        if await alert_rows.count() > 0:
            await alert_rows.first.click()
        else:
            # just click anything that looks like an alert or table row
            await page.locator("li").first.click(timeout=1000)
            
        await page.wait_for_timeout(2000)
        print("Taking SHAP chart screenshot...")
        await page.screenshot(path="test_screenshots/tc08_shap_chart.png")
        
        # Close modal
        close_btn = page.locator("button", has_text="Close")
        if await close_btn.count() > 0:
            await close_btn.first.click()
        else:
            await page.keyboard.press("Escape")
            
        await page.wait_for_timeout(1000)
        
        # 3. Credit scoring panel screenshot (TC-13)
        print("Taking credit scoring panel screenshot...")
        # We can just screenshot the whole dashboard again or specifically the panel
        panel = page.locator(".credit-scoring-panel, :text('Credit Scoring')").first
        if await panel.count() > 0:
            await panel.screenshot(path="test_screenshots/tc13_credit_scoring.png")
        else:
            await page.screenshot(path="test_screenshots/tc13_credit_scoring.png")
            
        await browser.close()
        print("Screenshots saved successfully.")

if __name__ == "__main__":
    asyncio.run(main())
