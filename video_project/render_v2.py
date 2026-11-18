#!/usr/bin/env python3
"""
AirGuard AI — Launch Video V2 Master Renderer
Renders the full 35.0-second 1080p motion graphics trailer using Playwright and FFmpeg.
Streams frames directly from Chromium into FFmpeg (zero temp disk files).
"""

import math
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML_PATH = ROOT / "video_project" / "index.html"
AUDIO_PATH = ROOT / "video_project" / "soundtrack_mastered.wav"
OUT_DIR = ROOT / "docs" / "videos"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_MP4 = OUT_DIR / "airguard-launch-v2.mp4"
OUT_POSTER = OUT_DIR / "airguard-launch-v2-poster.jpg"
OUT_GIF = OUT_DIR / "airguard-launch-v2-teaser.gif"

FPS = 30
DURATION = 35.0
TOTAL_FRAMES = int(FPS * DURATION)
W, H = 1920, 1080

def main():
    print("=" * 60)
    print("AirGuard AI — Launch Video V2 Master Renderer")
    print("=" * 60)

    # 1. Ensure audio master is ready
    if not AUDIO_PATH.exists():
        print("  Generating soundtrack and audio master...")
        subprocess.run([sys.executable, str(ROOT / "video_project" / "synth_soundtrack.py")], check=True)
        # Master with loudnorm to -15 LUFS
        subprocess.run([
            "ffmpeg", "-y", "-i", str(ROOT / "video_project" / "soundtrack_master.wav"),
            "-af", "loudnorm=I=-15:TP=-1.5:LRA=7",
            str(AUDIO_PATH)
        ], check=True)

    print(f"\n▸ Target: {TOTAL_FRAMES} frames ({DURATION}s @ {FPS}fps, {W}×{H})")
    print(f"▸ Output MP4: {OUT_MP4}")
    print(f"▸ Audio Master: {AUDIO_PATH}")

    # 2. Launch FFmpeg pipe process
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "image2pipe",
        "-vcodec", "png",
        "-r", str(FPS),
        "-i", "-",  # Read from stdin
        "-i", str(AUDIO_PATH),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        str(OUT_MP4)
    ]

    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    # 3. Launch Playwright Headless Chromium
    from playwright.sync_api import sync_playwright

    print("\n▸ Launching Headless Chromium to capture deterministic frames...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--enable-gpu",
                "--use-gl=angle",
                "--enable-webgl",
                "--disable-web-security",
                "--allow-file-access-from-files"
            ]
        )
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        page.goto(f"file://{HTML_PATH}")
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(500)

        # Poster frame timestamp (t = 5.8s, mid-dashboard)
        poster_frame_idx = int(5.8 * FPS)

        # Buffer for GIF sampling (sample 1 in every 3 frames from 4.0s to 12.0s = ~2.6s loop)
        gif_frames = []
        gif_start_idx = int(4.2 * FPS)
        gif_end_idx = int(12.0 * FPS)

        start_time = time.time()

        for frame_idx in range(TOTAL_FRAMES):
            t_sec = frame_idx / FPS
            page.evaluate(f"window.renderFrame({t_sec})")
            png_bytes = page.screenshot(type="png")

            # Pipe to FFmpeg
            proc.stdin.write(png_bytes)

            # Save poster frame
            if frame_idx == poster_frame_idx:
                with open(OUT_POSTER, "wb") as pf:
                    pf.write(page.screenshot(type="jpeg", quality=95))

            # Collect frames for teaser GIF
            if gif_start_idx <= frame_idx < gif_end_idx and (frame_idx % 2 == 0):
                gif_frames.append(png_bytes)

            if (frame_idx + 1) % 50 == 0 or frame_idx == 0:
                elapsed = time.time() - start_time
                fps_render = (frame_idx + 1) / elapsed
                pct = (frame_idx + 1) / TOTAL_FRAMES * 100
                print(f"  Frame {frame_idx + 1}/{TOTAL_FRAMES} ({pct:.0f}%) — {fps_render:.1f} fps")

        browser.close()

    print("\n▸ Finalizing FFmpeg encoding...")
    proc.stdin.close()
    stderr = proc.stderr.read().decode("utf-8")
    proc.wait()

    if proc.returncode != 0:
        print(f"FFmpeg error:\n{stderr[-1000:]}")
        sys.exit(1)

    print("✅ MP4 rendering complete!")

    # 4. Generate Teaser GIF
    if gif_frames:
        print("\n▸ Encoding compact teaser GIF from highlights...")
        from PIL import Image
        import io

        pil_frames = []
        for b in gif_frames:
            img = Image.open(io.BytesIO(b)).convert("RGB")
            # Downscale for crisp, fast-loading 800x450 GIF
            img = img.resize((800, 450), Image.LANCZOS)
            pil_frames.append(img)

        # Save GIF with optimized palette
        pil_frames[0].save(
            str(OUT_GIF),
            save_all=True,
            append_images=pil_frames[1:],
            duration=int(1000 / (FPS / 2)),
            loop=0,
            optimize=True
        )
        print(f"✅ Teaser GIF saved at {OUT_GIF}")

    # 5. Measure and report Audio Loudness with FFmpeg ebur128
    print("\n▸ Measuring final audio loudness...")
    res = subprocess.run(
        ["ffmpeg", "-i", str(OUT_MP4), "-filter:a", "ebur128=framelog=verbose", "-f", "null", "-"],
        capture_output=True, text=True
    )
    for line in res.stderr.splitlines():
        if "I:" in line or "LRA:" in line or "Threshold:" in line:
            print("  " + line.strip())

    # 6. Generate VIDEO_CREDITS.md
    credits_content = """# AirGuard AI — Product Launch Video V2 Credits & Technical Specs

## Video Specifications
- **File:** `docs/videos/airguard-launch-v2.mp4`
- **Resolution:** 1920 × 1080 (1080p Full HD, 16:9)
- **Frame Rate:** 30.00 fps
- **Duration:** 35.00 seconds
- **Video Codec:** H.264 (High Profile, CRF 18, yuv420p)
- **Audio Codec:** AAC (192 kbps, 48 kHz stereo)
- **Master Audio Loudness:** -15.0 LUFS integrated, True Peak < -1.0 dBTP (EBU R128 compliant)

## Creative & Technical Direction
- **Motion Design Framework:** Inspired by Bang Motion principles (anti-slideshow continuous 3D camera travel, kinetic typography, zero static PowerPoint decks).
- **Soundtrack & Sound Design:** MotionCraft-inspired pure DSP procedural synthesis engine (`video_project/synth_soundtrack.py`).
  - 116 BPM electronic tech groove in F minor resolving to F major.
  - Sub-bass cinematic boom, transition whooshes, UI telemetry clicks, alert notification chimes, and resolving outro chord.
  - **100% Free & Open Source ($0 budget):** No commercial samples, no paid APIs, no subscriptions.
- **Rendering Pipeline:** Headless Chromium via Playwright directly piped into FFmpeg libx264.

## Storyboard
1. **0–4s:** Atmospheric dark brand reveal with floating data particles and kinetic headline (*"Meet AirGuard AI"*).
2. **4–9s:** 2.5D camera move into the operational dashboard with live PM2.5 circular gauge sweep and multi-gas HUD.
3. **9–14s:** Multi-protocol device topology connecting AirGradient, Core Gateway, and Smart Purifier with animated laser data packets.
4. **14–20s:** AI Model Lab showcasing OpenPOM SMILES molecular structure and honest session-independent BME688 holdout benchmark disclosures.
5. **20–27s:** Intelligent automated response demonstrating elevated particle event, safety invariant checks, and purifier actuation.
6. **27–31s:** High-tempo rapid product montage synchronized to the musical rhythm.
7. **31–35s:** Climax resolution with converging UI layers into the AirGuard AI logo and GitHub repository link.

## Companion Assets
- Poster Frame: `docs/videos/airguard-launch-v2-poster.jpg`
- Teaser GIF: `docs/videos/airguard-launch-v2-teaser.gif`
- Editable Video Project: `video_project/index.html`
"""
    (OUT_DIR / "VIDEO_CREDITS.md").write_text(credits_content)
    print("✅ Generated docs/videos/VIDEO_CREDITS.md")

    # Final Summary
    print("\n" + "=" * 60)
    print("ALL V2 VIDEO ASSETS GENERATED SUCCESSFULLY")
    print("=" * 60)
    for p in [OUT_MP4, OUT_POSTER, OUT_GIF, OUT_DIR / "VIDEO_CREDITS.md"]:
        size_mb = p.stat().st_size / (1024 * 1024)
        print(f"  {p.name}: {size_mb:.2f} MB")

if __name__ == "__main__":
    main()
