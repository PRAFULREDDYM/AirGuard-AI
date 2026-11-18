"""
AirGuard AI — Portfolio Asset Generator
Captures high-resolution retina screenshots and animated walkthrough GIFs
for public release in docs/assets/.
"""

import asyncio
import os
import io
from PIL import Image
from playwright.async_api import async_playwright

FRONTEND_URL = "http://localhost:3000"
ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs", "assets"))

os.makedirs(ASSETS_DIR, exist_ok=True)

def save_gif(frame_bytes_list, output_path, duration=1500, loop=0):
    images = []
    for b in frame_bytes_list:
        img = Image.open(io.BytesIO(b)).convert("RGB")
        # Resize to reasonable dimensions for GitHub README (max width 960px)
        w, h = img.size
        target_w = 960
        target_h = int(h * (target_w / w))
        img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        # Quantize with palette
        img = img.quantize(colors=128, method=Image.Quantize.MEDIANCUT)
        images.append(img)
    
    if images:
        images[0].save(
            output_path,
            save_all=True,
            append_images=images[1:],
            optimize=True,
            duration=duration,
            loop=loop
        )
        print(f"  ✓ Saved GIF: {output_path} ({len(images)} frames)")

async def main():
    print(f"--- Starting Portfolio Asset Generation to {ASSETS_DIR} ---")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # 1. Desktop Context (Retina Scale for crisp text)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 840},
            device_scale_factor=2
        )
        page = await context.new_page()

        # -------------------------------------------------------------
        # 1. Dashboard Screenshot (docs/assets/dashboard.png)
        # -------------------------------------------------------------
        print("\n1. Capturing Dashboard Screenshot...")
        await page.goto(f"{FRONTEND_URL}/", wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        dash_path = os.path.join(ASSETS_DIR, "dashboard.png")
        await page.screenshot(path=dash_path, full_page=False)
        print(f"  ✓ Saved {dash_path}")

        # -------------------------------------------------------------
        # 2. Devices Page Screenshot (docs/assets/devices.png)
        # -------------------------------------------------------------
        print("\n2. Capturing Devices Page Screenshot...")
        await page.goto(f"{FRONTEND_URL}/devices", wait_until="domcontentloaded")
        await page.wait_for_timeout(1500)
        devices_path = os.path.join(ASSETS_DIR, "devices.png")
        await page.screenshot(path=devices_path, full_page=False)
        print(f"  ✓ Saved {devices_path}")

        # -------------------------------------------------------------
        # 3. AI Model Lab Screenshot (docs/assets/model-lab.png)
        # -------------------------------------------------------------
        print("\n3. Capturing AI Model Lab Screenshot...")
        await page.goto(f"{FRONTEND_URL}/models", wait_until="domcontentloaded")
        await page.wait_for_timeout(1000)
        # Input Isoamyl Acetate SMILES: CC(=O)OCCC(C)C
        try:
            smiles_input = page.locator('input[placeholder*="SMILES"]').first
            if await smiles_input.count() > 0:
                await smiles_input.fill("CC(=O)OCCC(C)C")
                predict_btn = page.locator('button:has-text("Predict"), button:has-text("Run Model")').first
                if await predict_btn.count() > 0:
                    await predict_btn.click()
                    await page.wait_for_timeout(1500)
        except Exception as e:
            print("  Note: Model Lab input interaction note:", e)

        model_path = os.path.join(ASSETS_DIR, "model-lab.png")
        await page.screenshot(path=model_path, full_page=False)
        print(f"  ✓ Saved {model_path}")

        # -------------------------------------------------------------
        # 4. Analytics Screenshot (docs/assets/analytics.png)
        # -------------------------------------------------------------
        print("\n4. Capturing Analytics Screenshot...")
        await page.goto(f"{FRONTEND_URL}/analytics", wait_until="domcontentloaded")
        await page.wait_for_timeout(1500)
        analytics_path = os.path.join(ASSETS_DIR, "analytics.png")
        await page.screenshot(path=analytics_path, full_page=False)
        print(f"  ✓ Saved {analytics_path}")

        # -------------------------------------------------------------
        # 5. Mobile Responsive Screenshot (docs/assets/mobile.png)
        # -------------------------------------------------------------
        print("\n5. Capturing Mobile Viewport Screenshot...")
        mobile_context = await browser.new_context(
            viewport={"width": 390, "height": 844},
            device_scale_factor=2,
            is_mobile=True,
            has_touch=True
        )
        mobile_page = await mobile_context.new_page()
        await mobile_page.goto(f"{FRONTEND_URL}/", wait_until="domcontentloaded")
        await mobile_page.wait_for_timeout(1500)
        mobile_path = os.path.join(ASSETS_DIR, "mobile.png")
        await mobile_page.screenshot(path=mobile_path, full_page=False)
        await mobile_context.close()
        print(f"  ✓ Saved {mobile_path}")

        # -------------------------------------------------------------
        # 6. Hero Demo GIF (docs/assets/hero-demo.gif)
        # -------------------------------------------------------------
        print("\n6. Recording Hero Demo GIF (Dashboard & Live Telemetry)...")
        demo_frames = []
        await page.goto(f"{FRONTEND_URL}/", wait_until="domcontentloaded")
        await page.wait_for_timeout(1000)
        # Frame 1: Normal Overview
        demo_frames.append(await page.screenshot())

        # Frame 2: Trigger Cooking Event simulation
        cooking_btn = page.locator('button:has-text("Cooking Event")').first
        if await cooking_btn.count() > 0:
            await cooking_btn.click()
            await page.wait_for_timeout(1000)
            demo_frames.append(await page.screenshot())
            await page.wait_for_timeout(1000)
            demo_frames.append(await page.screenshot())

        # Frame 3: Navigate to Rooms view
        await page.goto(f"{FRONTEND_URL}/rooms", wait_until="domcontentloaded")
        await page.wait_for_timeout(1000)
        demo_frames.append(await page.screenshot())

        # Frame 4: Return to normal dashboard
        await page.goto(f"{FRONTEND_URL}/", wait_until="domcontentloaded")
        await page.wait_for_timeout(800)
        normal_btn = page.locator('button:has-text("Normal")').first
        if await normal_btn.count() > 0:
            await normal_btn.click()
            await page.wait_for_timeout(800)
        demo_frames.append(await page.screenshot())

        save_gif(demo_frames, os.path.join(ASSETS_DIR, "hero-demo.gif"), duration=1400)

        # -------------------------------------------------------------
        # 7. Onboarding Walkthrough GIF (docs/assets/onboarding.gif)
        # -------------------------------------------------------------
        print("\n7. Recording Onboarding Wizard Walkthrough GIF (8 Stages)...")
        ob_frames = []
        await page.goto(f"{FRONTEND_URL}/onboarding", wait_until="domcontentloaded")
        await page.wait_for_timeout(1000)
        # Stage 1
        ob_frames.append(await page.screenshot())

        # Stage 2
        await page.locator('button:has-text("Continue to Connect Devices")').click()
        await page.wait_for_timeout(800)
        ob_frames.append(await page.screenshot())

        # Stage 3
        await page.locator('button:has-text("Verify & Authenticate")').click()
        await page.wait_for_timeout(1200)
        ob_frames.append(await page.screenshot())

        # Stage 4
        await page.locator('button:has-text("Assign Room")').click()
        await page.wait_for_timeout(800)
        ob_frames.append(await page.screenshot())

        # Stage 5
        await page.locator('button:has-text("Select Operating Mode")').click()
        await page.wait_for_timeout(800)
        ob_frames.append(await page.screenshot())

        # Stage 6
        await page.locator('button:has-text("Permissions")').click()
        await page.wait_for_timeout(800)
        ob_frames.append(await page.screenshot())

        # Stage 7
        await page.locator('button:has-text("Continue to Test")').click()
        await page.wait_for_timeout(800)
        ob_frames.append(await page.screenshot())

        # Stage 8
        await page.locator('button:has-text("Review & Activate")').click()
        await page.wait_for_timeout(800)
        ob_frames.append(await page.screenshot())

        save_gif(ob_frames, os.path.join(ASSETS_DIR, "onboarding.gif"), duration=1600)

        # -------------------------------------------------------------
        # 8. Automations & Safety Controls GIF (docs/assets/automations.gif)
        # -------------------------------------------------------------
        print("\n8. Recording Automations & Safety Controls GIF...")
        auto_frames = []
        await page.goto(f"{FRONTEND_URL}/automations", wait_until="domcontentloaded")
        await page.wait_for_timeout(1000)
        auto_frames.append(await page.screenshot())

        # Frame 2: Click emergency pause kill switch in navbar
        pause_btn = page.locator('button:has-text("Pause All Automations")').first
        if await pause_btn.count() > 0:
            await pause_btn.click()
            await page.wait_for_timeout(1000)
            auto_frames.append(await page.screenshot())

            # Frame 3: Resume automations
            resume_btn = page.locator('button:has-text("Resume Automations")').first
            if await resume_btn.count() > 0:
                await resume_btn.click()
                await page.wait_for_timeout(1000)
                auto_frames.append(await page.screenshot())

        save_gif(auto_frames, os.path.join(ASSETS_DIR, "automations.gif"), duration=1500)

        await browser.close()
        print("\n✓ Playwright asset capture complete!")

if __name__ == "__main__":
    asyncio.run(main())
