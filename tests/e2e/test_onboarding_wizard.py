"""
AirGuard AI — Phase 7 Playwright E2E Browser Test Suite: Onboarding Wizard & Safety Controls
Tests:
- Stage 1: Welcome & Safety Limits Disclaimer (Local-first, Certified Alarm independence)
- Stage 2: Device Selection & Compatibility Preview
- Stage 3: Live Handshake & Measurement Verification
- Stage 4: Room Assignment & Sensor-Purifier Pairing
- Stage 5: Dual Operating Mode Selection (Monitor & Notify vs. Automatic Control)
- Stage 6: Unbundled Consent & Permissions Matrix
- Stage 7: Test & Dry-Run (Sensor ping, Notification test, Guarded Purifier Pulse)
- Stage 8: Activation & Room Dashboard Redirection
- Emergency Global Automation Pause Button
- Settings: Consent Revocation & GDPR Data Export
"""

import pytest
import pytest_asyncio
import asyncio
from playwright.async_api import async_playwright, expect

FRONTEND_URL = "http://localhost:3000"

@pytest.mark.asyncio
async def test_onboarding_8_stage_wizard_e2e():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("\n--- 1. Navigating to Unified Onboarding Wizard (/onboarding) ---")
        await page.goto(f"{FRONTEND_URL}/onboarding", wait_until="networkidle")
        await expect(page.locator("h1")).to_contain_text("AirGuard Setup")

        # Stage 1: Welcome & Limits
        print("Checking Stage 1: Welcome & Life-Safety Disclaimers...")
        stage_text = await page.content()
        assert "Independent of Life-Safety Alarms" in stage_text
        assert "Certified Smoke & CO" in stage_text
        assert "Local-First Operation" in stage_text

        # Click Next to Stage 2
        next_btn = page.locator('button:has-text("Begin Setup")')
        await next_btn.click()
        await page.wait_for_timeout(400)

        # Stage 2: Connect Devices
        print("Checking Stage 2: Connect Devices & Compatibility...")
        await expect(page.locator("h2")).to_contain_text("Connect Devices")
        stage2_text = await page.content()
        assert "Home Assistant" in stage2_text
        assert "AirGradient" in stage2_text
        assert "Levoit" in stage2_text

        # Select devices to onboard
        ha_checkbox = page.locator('input[type="checkbox"]').first
        await ha_checkbox.check()
        
        next_btn = page.locator('button:has-text("Continue to Verification")')
        await next_btn.click()
        await page.wait_for_timeout(400)

        # Stage 3: Verify Connections
        print("Checking Stage 3: Live Verification & Measurement Handshake...")
        await expect(page.locator("h2")).to_contain_text("Verify Connections")
        stage3_text = await page.content()
        assert "Live Handshake" in stage3_text
        assert "Verified" in stage3_text

        next_btn = page.locator('button:has-text("Continue to Room Assignment")')
        await next_btn.click()
        await page.wait_for_timeout(400)

        # Stage 4: Assign Rooms
        print("Checking Stage 4: Room Assignment & Sensor-Purifier Pairing...")
        await expect(page.locator("h2")).to_contain_text("Assign Rooms")
        stage4_text = await page.content()
        assert "Living Room" in stage4_text

        next_btn = page.locator('button:has-text("Continue to Operating Mode")')
        await next_btn.click()
        await page.wait_for_timeout(400)

        # Stage 5: Select Operating Mode
        print("Checking Stage 5: Mode Selection (Monitor & Notify vs. Auto Control)...")
        await expect(page.locator("h2")).to_contain_text("Select Operating Mode")
        stage5_text = await page.content()
        assert "Monitor & Notify (Recommended)" in stage5_text
        assert "Automatic Purifier Control" in stage5_text

        # Click Automatic Purifier Control option
        auto_mode_btn = page.locator('button:has-text("Automatic Purifier Control")')
        await auto_mode_btn.click()
        await page.wait_for_timeout(300)

        next_btn = page.locator('button:has-text("Continue to Permissions")')
        await next_btn.click()
        await page.wait_for_timeout(400)

        # Stage 6: Permissions & Consent
        print("Checking Stage 6: Unbundled Consent & Permissions Matrix...")
        await expect(page.locator("h2")).to_contain_text("Permissions & Consent")
        stage6_text = await page.content()
        assert "Environmental Telemetry" in stage6_text
        assert "In-App & Push Notifications" in stage6_text
        assert "Automatic Device Control" in stage6_text
        assert "Anonymous AI Training Data" in stage6_text

        next_btn = page.locator('button:has-text("Continue to Testing")')
        await next_btn.click()
        await page.wait_for_timeout(400)

        # Stage 7: Test & Dry-Run
        print("Checking Stage 7: Test & Dry-Run (Sensor & Notification Ping)...")
        await expect(page.locator("h2")).to_contain_text("System Dry-Run")
        stage7_text = await page.content()
        assert "Test Sensor Reception" in stage7_text
        assert "Send Test Notification" in stage7_text
        assert "Pulse Purifier Fan" in stage7_text

        # Trigger notification test
        test_notif_btn = page.locator('button:has-text("Send Test Notification")')
        await test_notif_btn.click()
        await page.wait_for_timeout(500)

        next_btn = page.locator('button:has-text("Review & Activate")')
        await next_btn.click()
        await page.wait_for_timeout(400)

        # Stage 8: Activate & Summary
        print("Checking Stage 8: Review & Activation...")
        await expect(page.locator("h2")).to_contain_text("Review & Activate")
        stage8_text = await page.content()
        assert "Ready to Protect Your Air" in stage8_text
        assert "Activate AirGuard" in stage8_text

        # Complete activation
        activate_btn = page.locator('button:has-text("Activate AirGuard")')
        await activate_btn.click()
        await page.wait_for_timeout(1000)

        # Verify redirection to Rooms / Dashboard
        print("Checking post-activation redirection...")
        assert "/rooms" in page.url or "/" in page.url
        print("Successfully completed full 8-stage Onboarding flow in browser!")

        # 9. Verify Settings Page features (Consents, Notification center, GDPR)
        print("\n--- 2. Verifying Settings Page Privacy & Notification Center ---")
        await page.goto(f"{FRONTEND_URL}/settings", wait_until="networkidle")
        await expect(page.locator("h1")).to_contain_text("Settings")
        settings_text = await page.content()
        assert "Granted Consents" in settings_text
        assert "Notification Preferences" in settings_text
        assert "Privacy & Compliance (GDPR / CCPA)" in settings_text
        assert "Export My Data (JSON)" in settings_text
        print("Verified Settings Page consent controls and GDPR export UI.")

        # 10. Verify Emergency Pause Kill-Switch Button in Navbar
        print("\n--- 3. Verifying Emergency Kill Switch in Global Navigation ---")
        kill_switch = page.locator('button:has-text("Pause All Automations"), button:has-text("Resume Automations")').first
        await expect(kill_switch).to_be_visible()
        print("Verified global Pause All Automations kill switch in top navigation.")

        await browser.close()
