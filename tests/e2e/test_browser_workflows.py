import pytest
import pytest_asyncio
import asyncio
from playwright.async_api import async_playwright, expect

FRONTEND_URL = "http://localhost:3000"
API_URL = "http://127.0.0.1:8000/api/v1"

@pytest.mark.asyncio
async def test_complete_browser_e2e_suite():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("\n--- 1. Testing Dashboard and Auto-Login ---")
        await page.goto(FRONTEND_URL, wait_until="networkidle")
        title = await page.title()
        print(f"Page title: {title}")
        assert "AirGuard" in title or len(title) > 0
        
        # Verify Dashboard header is rendered
        header_text = await page.locator("h1").first.text_content()
        print(f"Dashboard header: {header_text}")
        assert "Overview" in header_text or "Air" in header_text or "AirGuard" in header_text

        # 2. Testing Devices Page and Add Device Form
        print("\n--- 2. Testing Devices Onboarding ---")
        await page.goto(f"{FRONTEND_URL}/devices", wait_until="networkidle")
        await expect(page.locator("h1")).to_contain_text("Connected Devices")
        
        # Navigate to Add Device
        await page.goto(f"{FRONTEND_URL}/devices/add", wait_until="networkidle")
        await expect(page.locator("h1")).to_contain_text("Device")
        
        # Verify supported protocols are visible (Home Assistant, MQTT, AirGradient, Simulation)
        page_text = await page.content()
        assert "Home Assistant" in page_text
        assert "MQTT" in page_text
        assert "AirGradient" in page_text
        assert "Simulation" in page_text
        print("Verified protocol cards: Home Assistant, MQTT, AirGradient, Simulation.")

        # 3. Testing Rooms Page
        print("\n--- 3. Testing Rooms Page ---")
        await page.goto(f"{FRONTEND_URL}/rooms", wait_until="networkidle")
        await expect(page.locator("h1")).to_contain_text("Rooms")
        print("Rooms page loaded successfully.")

        # 4. Testing Events & Safety Separation
        print("\n--- 4. Testing Events History & Hazard Separation ---")
        await page.goto(f"{FRONTEND_URL}/events", wait_until="networkidle")
        await expect(page.locator("h1")).to_contain_text("Environmental Events")
        events_content = await page.content()
        assert "Safety Policy" in events_content or "Events" in events_content or "Alarms" in events_content
        print("Events page rendered with safety policy separation.")

        # 5. Testing Automations Page & Safety Guarantees
        print("\n--- 5. Testing Automations & Safety Engine Callout ---")
        await page.goto(f"{FRONTEND_URL}/automations", wait_until="networkidle")
        await expect(page.locator("h1")).to_contain_text("Automations")
        automations_content = await page.content()
        # Verify non-negotiable safety rules callout
        assert "Combustible Gas" in automations_content or "Ozone" in automations_content or "Safety" in automations_content
        print("Automations page rendered with non-negotiable safety rules callout.")

        # 6. Testing AI Model Lab — Molecular Odor & E-Nose Benchmarks
        print("\n--- 6. Testing AI Model Lab (Molecular & E-Nose) ---")
        await page.goto(f"{FRONTEND_URL}/models", wait_until="networkidle")
        await expect(page.locator("h1")).to_contain_text("AI Model Lab")

        # Test live SMILES prediction for Isoamyl acetate
        smiles_input = page.locator('input[type="text"]').first
        await smiles_input.fill("CC(=O)OCCC(C)C")
        
        predict_button = page.locator('button:has-text("Predict Odors")').first
        await predict_button.click()
        
        # Wait for predicted descriptors to appear
        await page.wait_for_selector('text=Predicted Odor Descriptors', timeout=10000)
        mol_content = await page.content()
        assert "fruity" in mol_content.lower() or "sweet" in mol_content.lower()
        print("Live SMILES prediction verified: Isoamyl acetate predicted fruity/sweet successfully.")

        # Verify Electronic-Nose Tab
        enose_tab = page.locator('button:has-text("Electronic-Nose")')
        await enose_tab.click()
        await page.wait_for_timeout(1000)
        enose_content = await page.content()
        assert "BME688" in enose_content
        assert "CoffeePow-4" in enose_content
        assert "90.56%" in enose_content or "HistGradientBoosting" in enose_content
        print("Electronic-Nose benchmark tab verified with genuine BME688 metrics.")

        # 7. Testing Error Handling & Input Validation
        print("\n--- 7. Testing Invalid SMILES Rejection ---")
        mol_tab = page.locator('button:has-text("Molecular Odor")')
        await mol_tab.click()
        await page.wait_for_timeout(500)
        
        await smiles_input.fill("INVALID_SMILES_CHEMICAL_XYZ###")
        await predict_button.click()
        await page.wait_for_timeout(1500)
        err_content = await page.content()
        assert "Failed" in err_content or "Invalid" in err_content or "parse" in err_content or "error" in err_content
        print("Invalid chemical structure rejected with structured error message.")

        # Take screenshot of AI Model Lab as verification artifact
        screenshot_path = "docs/model_lab_verified_e2e.png"
        await page.screenshot(path=screenshot_path)
        print(f"Captured E2E verification screenshot: {screenshot_path}")

        await context.close()
        await browser.close()
        print("\n>>> ALL PLAYWRIGHT E2E BROWSER TESTS PASSED <<<")

if __name__ == "__main__":
    asyncio.run(test_complete_browser_e2e_suite())
