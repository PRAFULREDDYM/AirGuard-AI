#!/usr/bin/env python3
"""
AirGuard AI — Cinematic Launch Video Renderer
Renders a 30-second 1920×1080 launch video using Pillow + FFmpeg.
$0 budget: no paid APIs, no network, no subscriptions.
"""

import math
import os
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "docs" / "assets"
OUT = ROOT / "docs" / "videos"
OUT.mkdir(parents=True, exist_ok=True)

FRAME_DIR = OUT / "_frames"
if FRAME_DIR.exists():
    shutil.rmtree(FRAME_DIR)
FRAME_DIR.mkdir()

W, H = 1920, 1080
FPS = 30
TOTAL_SECONDS = 30
TOTAL_FRAMES = FPS * TOTAL_SECONDS

# ── Colors ─────────────────────────────────────────────────────────────────
BG_DARK = (10, 10, 18)
ACCENT_TEAL = (0, 200, 180)
ACCENT_BLUE = (60, 130, 246)
WHITE = (255, 255, 255)
LIGHT_GRAY = (180, 180, 195)
OVERLAY_BLACK = (0, 0, 0, 160)
SIMULATION_YELLOW = (255, 200, 0)

# ── Fonts ──────────────────────────────────────────────────────────────────
def load_font(size, bold=False):
    """Load SF Pro or Avenir Next or fall back gracefully."""
    candidates = [
        "/System/Library/Fonts/SFNSDisplay.ttf",
        "/System/Library/Fonts/SFNS.ttf",
        "/Library/Fonts/SF-Pro-Display-Regular.otf",
    ]
    if bold:
        candidates = [
            "/System/Library/Fonts/SFNSDisplayBold.ttf",
            "/Library/Fonts/SF-Pro-Display-Bold.otf",
        ] + candidates

    # Try Avenir Next as fallback
    candidates += [
        "/System/Library/Fonts/Avenir Next.ttc",
        "/System/Library/Fonts/Supplemental/Avenir Next.ttc",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/HelveticaNeue.ttc",
    ]

    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                continue
    return ImageFont.load_default()


FONT_HERO = load_font(72, bold=True)
FONT_SUB = load_font(36)
FONT_SMALL = load_font(24)
FONT_TAG = load_font(18, bold=True)
FONT_LARGE = load_font(96, bold=True)

# ── Screenshot cache ───────────────────────────────────────────────────────
_img_cache = {}

def load_screenshot(name):
    """Load an asset, resize to fit 1920×1080, center on dark bg."""
    if name in _img_cache:
        return _img_cache[name]
    path = ASSETS / name
    if not path.exists():
        # Return a dark placeholder
        img = Image.new("RGB", (W, H), BG_DARK)
        _img_cache[name] = img
        return img

    src = Image.open(path).convert("RGB")
    # Scale to fit within 1920×1080 preserving aspect ratio
    src_w, src_h = src.size
    scale = min(W / src_w, H / src_h)
    new_w = int(src_w * scale)
    new_h = int(src_h * scale)
    src = src.resize((new_w, new_h), Image.LANCZOS)

    canvas = Image.new("RGB", (W, H), BG_DARK)
    x = (W - new_w) // 2
    y = (H - new_h) // 2
    canvas.paste(src, (x, y))
    _img_cache[name] = canvas
    return canvas


def load_logo():
    """Load the AirGuard logo, center it."""
    if "logo" in _img_cache:
        return _img_cache["logo"]
    path = ASSETS / "airguard-logo.png"
    if not path.exists():
        img = Image.new("RGBA", (600, 160), (0, 0, 0, 0))
        _img_cache["logo"] = img
        return img
    src = Image.open(path).convert("RGBA")
    # Scale to reasonable size
    target_w = 800
    scale = target_w / src.width
    new_h = int(src.height * scale)
    src = src.resize((target_w, new_h), Image.LANCZOS)
    _img_cache["logo"] = src
    return src


# ── Drawing helpers ────────────────────────────────────────────────────────
def ease_in_out(t):
    """Smooth ease-in-out cubic."""
    if t < 0.5:
        return 4 * t * t * t
    return 1 - pow(-2 * t + 2, 3) / 2


def draw_gradient_bg(draw, color_top=BG_DARK, color_bottom=(15, 20, 40)):
    """Vertical dark gradient."""
    for y in range(H):
        t = y / H
        r = int(color_top[0] + (color_bottom[0] - color_top[0]) * t)
        g = int(color_top[1] + (color_bottom[1] - color_top[1]) * t)
        b = int(color_top[2] + (color_bottom[2] - color_top[2]) * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))


def draw_centered_text(draw, y, text, font, fill=WHITE, shadow=True):
    """Draw horizontally centered text with optional drop shadow."""
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    x = (W - tw) // 2
    if shadow:
        draw.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0, 128))
    draw.text((x, y), text, font=font, fill=fill)


def draw_accent_line(draw, y, width=200, color=ACCENT_TEAL):
    """Draw a centered accent underline."""
    x = (W - width) // 2
    draw.rectangle([(x, y), (x + width, y + 3)], fill=color)


def draw_simulation_badge(draw, text="SIMULATION / DEMO"):
    """Small badge in bottom-right."""
    font = FONT_TAG
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    pad = 8
    x = W - tw - pad * 2 - 20
    y = H - th - pad * 2 - 20
    draw.rectangle([(x, y), (x + tw + pad * 2, y + th + pad * 2)],
                   fill=(0, 0, 0, 180), outline=SIMULATION_YELLOW)
    draw.text((x + pad, y + pad), text, font=font, fill=SIMULATION_YELLOW)


def overlay_darken(base, alpha=0.4):
    """Apply a dark overlay on a screenshot for text readability."""
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, int(255 * alpha)))
    if base.mode != "RGBA":
        base = base.convert("RGBA")
    result = Image.alpha_composite(base, overlay)
    return result.convert("RGB")


def crossfade(img_a, img_b, t):
    """Blend two RGB images. t=0 → img_a, t=1 → img_b."""
    t = max(0.0, min(1.0, t))
    return Image.blend(img_a, img_b, t)


def ken_burns(img, t, zoom_start=1.0, zoom_end=1.08):
    """Subtle Ken Burns zoom effect. t in [0,1]."""
    zoom = zoom_start + (zoom_end - zoom_start) * t
    cw = int(W / zoom)
    ch = int(H / zoom)
    # Pan slightly right and down
    pan_x = int((W - cw) * 0.3 * t)
    pan_y = int((H - ch) * 0.4 * t)
    crop = img.crop((pan_x, pan_y, pan_x + cw, pan_y + ch))
    return crop.resize((W, H), Image.LANCZOS)


# ── Animated particles (simple floating dots) ─────────────────────────────
class Particle:
    def __init__(self, seed):
        import random
        rng = random.Random(seed)
        self.x = rng.uniform(0, W)
        self.y = rng.uniform(0, H)
        self.vx = rng.uniform(-0.3, 0.3)
        self.vy = rng.uniform(-0.5, -0.1)
        self.size = rng.randint(2, 5)
        self.alpha_base = rng.randint(40, 120)
        self.phase = rng.uniform(0, 2 * math.pi)

    def draw(self, draw_obj, frame):
        x = (self.x + self.vx * frame) % W
        y = (self.y + self.vy * frame) % H
        alpha = int(self.alpha_base * (0.5 + 0.5 * math.sin(frame * 0.05 + self.phase)))
        color = (*ACCENT_TEAL[:3], alpha)
        r = self.size
        draw_obj.ellipse([(x - r, y - r), (x + r, y + r)], fill=color)


PARTICLES = [Particle(i) for i in range(30)]

def draw_particles(draw_obj, frame):
    for p in PARTICLES:
        p.draw(draw_obj, frame)


# ── Segment renderers ─────────────────────────────────────────────────────
# Each returns an RGB Image for the given frame within its segment.

def segment_intro(frame, seg_frames):
    """0–5s: Dark background, logo animation, 'Meet AirGuard AI'."""
    t = frame / seg_frames  # 0→1
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw_gradient_bg(draw)
    draw_particles(draw, frame)

    logo = load_logo()
    # Fade in logo (0 → 0.3)
    logo_alpha = min(1.0, t / 0.3) if t < 0.3 else 1.0
    # Slight upward motion
    logo_y = int(260 + 30 * (1 - ease_in_out(min(1.0, t / 0.4))))
    logo_x = (W - logo.width) // 2

    if logo_alpha < 1.0:
        logo_fade = logo.copy()
        alpha_channel = logo_fade.split()[3]
        alpha_channel = alpha_channel.point(lambda p: int(p * logo_alpha))
        logo_fade.putalpha(alpha_channel)
        img.paste(logo_fade, (logo_x, logo_y), logo_fade)
    else:
        img.paste(logo, (logo_x, logo_y), logo)

    # Title text fades in at t=0.25
    title_t = max(0, (t - 0.25) / 0.3)
    title_t = min(1.0, title_t)
    if title_t > 0:
        title_alpha = int(255 * ease_in_out(title_t))
        title_y = int(520 + 20 * (1 - ease_in_out(title_t)))
        text = "Meet AirGuard AI"
        bbox = draw.textbbox((0, 0), text, font=FONT_HERO)
        tw = bbox[2] - bbox[0]
        tx = (W - tw) // 2
        draw.text((tx, title_y), text, font=FONT_HERO,
                  fill=(*WHITE, title_alpha))

    # Subtitle fades in at t=0.5
    sub_t = max(0, (t - 0.5) / 0.3)
    sub_t = min(1.0, sub_t)
    if sub_t > 0:
        sub_alpha = int(255 * ease_in_out(sub_t))
        text2 = "Intelligent Air Quality Monitoring & Response"
        bbox2 = draw.textbbox((0, 0), text2, font=FONT_SUB)
        tw2 = bbox2[2] - bbox2[0]
        tx2 = (W - tw2) // 2
        draw.text((tx2, 610), text2, font=FONT_SUB,
                  fill=(*LIGHT_GRAY, sub_alpha))
        # Accent line
        if sub_t > 0.5:
            line_w = int(200 * min(1.0, (sub_t - 0.5) * 2))
            lx = (W - line_w) // 2
            draw.rectangle([(lx, 660), (lx + line_w, 663)],
                          fill=(*ACCENT_TEAL, sub_alpha))

    return img.convert("RGB")


def segment_dashboard(frame, seg_frames):
    """5–10s: Dashboard with Ken Burns, 'Monitor your environment.'"""
    t = frame / seg_frames
    base = load_screenshot("dashboard.png")
    base = ken_burns(base, t, 1.0, 1.06)
    base = overlay_darken(base, 0.35)

    img = base.convert("RGBA")
    draw = ImageDraw.Draw(img)

    # Text fade-in
    text_t = max(0, (t - 0.1) / 0.3)
    text_t = min(1.0, text_t)
    if text_t > 0:
        alpha = int(255 * ease_in_out(text_t))
        text = "Monitor your environment."
        bbox = draw.textbbox((0, 0), text, font=FONT_HERO)
        tw = bbox[2] - bbox[0]
        tx = (W - tw) // 2
        # Drop shadow
        draw.text((tx + 2, H - 180 + 2), text, font=FONT_HERO,
                  fill=(0, 0, 0, alpha))
        draw.text((tx, H - 180), text, font=FONT_HERO,
                  fill=(*WHITE, alpha))

        # Accent underline
        if text_t > 0.5:
            lw = int(300 * min(1.0, (text_t - 0.5) * 2))
            lx = (W - lw) // 2
            draw.rectangle([(lx, H - 110), (lx + lw, H - 107)],
                          fill=(*ACCENT_TEAL, alpha))

    draw_simulation_badge(draw)
    return img.convert("RGB")


def segment_devices(frame, seg_frames):
    """10–15s: Device onboarding & connectivity."""
    t = frame / seg_frames
    base = load_screenshot("devices.png")
    base = ken_burns(base, t, 1.0, 1.05)
    base = overlay_darken(base, 0.4)

    img = base.convert("RGBA")
    draw = ImageDraw.Draw(img)

    text_t = max(0, (t - 0.1) / 0.3)
    text_t = min(1.0, text_t)
    if text_t > 0:
        alpha = int(255 * ease_in_out(text_t))
        text = "Connect compatible smart-home devices."
        bbox = draw.textbbox((0, 0), text, font=FONT_SUB)
        tw = bbox[2] - bbox[0]
        tx = (W - tw) // 2
        draw.text((tx + 2, H - 160 + 2), text, font=FONT_SUB,
                  fill=(0, 0, 0, alpha))
        draw.text((tx, H - 160), text, font=FONT_SUB,
                  fill=(*WHITE, alpha))

    # Feature pills
    pill_t = max(0, (t - 0.4) / 0.3)
    pill_t = min(1.0, pill_t)
    if pill_t > 0:
        alpha = int(255 * ease_in_out(pill_t))
        pills = ["Home Assistant", "MQTT", "AirGradient", "ESPHome"]
        total_w = sum(len(p) * 12 + 40 for p in pills) + 15 * (len(pills) - 1)
        px = (W - total_w) // 2
        py = H - 100
        for pill_text in pills:
            bbox = draw.textbbox((0, 0), pill_text, font=FONT_SMALL)
            pw = bbox[2] - bbox[0] + 30
            ph = 36
            draw.rounded_rectangle(
                [(px, py), (px + pw, py + ph)],
                radius=18,
                fill=(0, 0, 0, min(180, alpha)),
                outline=(*ACCENT_TEAL, alpha)
            )
            draw.text((px + 15, py + 6), pill_text, font=FONT_SMALL,
                      fill=(*ACCENT_TEAL, alpha))
            px += pw + 15

    draw_simulation_badge(draw)
    return img.convert("RGB")


def segment_model_lab(frame, seg_frames):
    """15–20s: AI Model Lab — molecular odor predictions."""
    t = frame / seg_frames
    base = load_screenshot("model-lab.png")
    base = ken_burns(base, t, 1.0, 1.05)
    base = overlay_darken(base, 0.35)

    img = base.convert("RGBA")
    draw = ImageDraw.Draw(img)

    text_t = max(0, (t - 0.1) / 0.3)
    text_t = min(1.0, text_t)
    if text_t > 0:
        alpha = int(255 * ease_in_out(text_t))
        text = "Explore AI-powered environmental intelligence."
        bbox = draw.textbbox((0, 0), text, font=FONT_SUB)
        tw = bbox[2] - bbox[0]
        tx = (W - tw) // 2
        draw.text((tx + 2, H - 160 + 2), text, font=FONT_SUB,
                  fill=(0, 0, 0, alpha))
        draw.text((tx, H - 160), text, font=FONT_SUB,
                  fill=(*WHITE, alpha))

    # Feature labels
    feat_t = max(0, (t - 0.5) / 0.3)
    feat_t = min(1.0, feat_t)
    if feat_t > 0:
        alpha = int(255 * ease_in_out(feat_t))
        feats = ["OpenPOM Molecular Models", "BME688 E-Nose Pipeline", "Session-Independent Splits"]
        total_w = sum(len(f) * 11 + 40 for f in feats) + 15 * (len(feats) - 1)
        px = (W - total_w) // 2
        py = H - 100
        for feat in feats:
            bbox = draw.textbbox((0, 0), feat, font=FONT_SMALL)
            fw = bbox[2] - bbox[0] + 30
            fh = 36
            draw.rounded_rectangle(
                [(px, py), (px + fw, py + fh)],
                radius=18,
                fill=(0, 0, 0, min(180, alpha)),
                outline=(*ACCENT_BLUE, alpha)
            )
            draw.text((px + 15, py + 6), feat, font=FONT_SMALL,
                      fill=(*ACCENT_BLUE, alpha))
            px += fw + 15

    draw_simulation_badge(draw)
    return img.convert("RGB")


def segment_automation(frame, seg_frames):
    """20–25s: Notifications & automation — 'From monitoring to action.'"""
    t = frame / seg_frames
    base = load_screenshot("analytics.png")
    base = ken_burns(base, t, 1.0, 1.06)
    base = overlay_darken(base, 0.4)

    img = base.convert("RGBA")
    draw = ImageDraw.Draw(img)

    text_t = max(0, (t - 0.1) / 0.3)
    text_t = min(1.0, text_t)
    if text_t > 0:
        alpha = int(255 * ease_in_out(text_t))
        text = "From monitoring to intelligent action."
        bbox = draw.textbbox((0, 0), text, font=FONT_HERO)
        tw = bbox[2] - bbox[0]
        tx = (W - tw) // 2
        ty = H // 2 - 60
        draw.text((tx + 2, ty + 2), text, font=FONT_HERO,
                  fill=(0, 0, 0, alpha))
        draw.text((tx, ty), text, font=FONT_HERO,
                  fill=(*WHITE, alpha))

    sub_t = max(0, (t - 0.4) / 0.3)
    sub_t = min(1.0, sub_t)
    if sub_t > 0:
        alpha2 = int(255 * ease_in_out(sub_t))
        sub = "Smart notifications  ·  Consent-based automation  ·  Safety-first controls"
        bbox2 = draw.textbbox((0, 0), sub, font=FONT_SMALL)
        tw2 = bbox2[2] - bbox2[0]
        tx2 = (W - tw2) // 2
        draw.text((tx2, H // 2 + 40), sub, font=FONT_SMALL,
                  fill=(*LIGHT_GRAY, alpha2))

    draw_simulation_badge(draw, "SIMULATION / DEMO — No live device control")
    return img.convert("RGB")


def segment_outro(frame, seg_frames):
    """25–30s: Closing — logo, tagline, GitHub URL."""
    t = frame / seg_frames
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw_gradient_bg(draw, (8, 8, 16), (12, 18, 35))
    draw_particles(draw, frame + 500)  # offset for variety

    logo = load_logo()

    # Logo fades in
    logo_alpha = min(1.0, t / 0.2)
    logo_y = 280
    logo_x = (W - logo.width) // 2

    if logo_alpha < 1.0:
        logo_fade = logo.copy()
        ac = logo_fade.split()[3]
        ac = ac.point(lambda p: int(p * logo_alpha))
        logo_fade.putalpha(ac)
        img.paste(logo_fade, (logo_x, logo_y), logo_fade)
    else:
        img.paste(logo, (logo_x, logo_y), logo)

    # Tagline
    tag_t = max(0, (t - 0.15) / 0.25)
    tag_t = min(1.0, tag_t)
    if tag_t > 0:
        alpha = int(255 * ease_in_out(tag_t))
        text = "Monitor.  Understand.  Respond."
        bbox = draw.textbbox((0, 0), text, font=FONT_SUB)
        tw = bbox[2] - bbox[0]
        tx = (W - tw) // 2
        draw.text((tx, 540), text, font=FONT_SUB,
                  fill=(*ACCENT_TEAL, alpha))

    # Accent line
    line_t = max(0, (t - 0.3) / 0.2)
    line_t = min(1.0, line_t)
    if line_t > 0:
        lw = int(400 * ease_in_out(line_t))
        lx = (W - lw) // 2
        la = int(255 * ease_in_out(line_t))
        draw.rectangle([(lx, 590), (lx + lw, 593)],
                      fill=(*ACCENT_TEAL, la))

    # GitHub URL
    url_t = max(0, (t - 0.4) / 0.25)
    url_t = min(1.0, url_t)
    if url_t > 0:
        alpha2 = int(255 * ease_in_out(url_t))
        url = "github.com/PRAFULREDDYM/AirGuard-AI"
        bbox2 = draw.textbbox((0, 0), url, font=FONT_SMALL)
        tw2 = bbox2[2] - bbox2[0]
        tx2 = (W - tw2) // 2
        draw.text((tx2, 640), url, font=FONT_SMALL,
                  fill=(*LIGHT_GRAY, alpha2))

    # Open source badge
    badge_t = max(0, (t - 0.55) / 0.2)
    badge_t = min(1.0, badge_t)
    if badge_t > 0:
        ba = int(255 * ease_in_out(badge_t))
        badge = "Open Source  ·  MIT License  ·  Python + Next.js"
        bbox3 = draw.textbbox((0, 0), badge, font=FONT_SMALL)
        tw3 = bbox3[2] - bbox3[0]
        tx3 = (W - tw3) // 2
        draw.text((tx3, 700), badge, font=FONT_SMALL,
                  fill=(*LIGHT_GRAY[:3], ba))

    # Final fade to black in last 1 second
    if t > 0.85:
        fade_t = (t - 0.85) / 0.15
        black = Image.new("RGBA", (W, H), (0, 0, 0, int(255 * fade_t)))
        img = Image.alpha_composite(img, black)

    return img.convert("RGB")


# ── Crossfade segments ─────────────────────────────────────────────────────
# Timeline: 6 segments of 5s each = 30s, with 0.5s crossfade between segments
SEGMENTS = [
    (0, 5, segment_intro),       # 0–5s
    (5, 10, segment_dashboard),  # 5–10s
    (10, 15, segment_devices),   # 10–15s
    (15, 20, segment_model_lab), # 15–20s
    (20, 25, segment_automation),# 20–25s
    (25, 30, segment_outro),     # 25–30s
]
CROSSFADE_FRAMES = int(0.5 * FPS)  # 15 frames = 0.5s crossfade


def render_frame(global_frame):
    """Render a single frame at a global frame index."""
    t_sec = global_frame / FPS

    # Find which segment we're in
    seg_idx = None
    for i, (start, end, _) in enumerate(SEGMENTS):
        if start <= t_sec < end:
            seg_idx = i
            break
    if seg_idx is None:
        seg_idx = len(SEGMENTS) - 1

    start, end, renderer = SEGMENTS[seg_idx]
    seg_duration = end - start
    seg_total_frames = int(seg_duration * FPS)
    local_frame = int((t_sec - start) * FPS)
    local_frame = max(0, min(local_frame, seg_total_frames - 1))

    img = renderer(local_frame, seg_total_frames)

    # Apply crossfade at segment boundaries
    frames_into_seg = local_frame
    if seg_idx > 0 and frames_into_seg < CROSSFADE_FRAMES:
        # Crossfade from previous segment
        prev_start, prev_end, prev_renderer = SEGMENTS[seg_idx - 1]
        prev_seg_frames = int((prev_end - prev_start) * FPS)
        prev_img = prev_renderer(prev_seg_frames - 1, prev_seg_frames)
        blend_t = frames_into_seg / CROSSFADE_FRAMES
        img = crossfade(prev_img, img, ease_in_out(blend_t))

    return img


# ── Audio synthesis ────────────────────────────────────────────────────────
def generate_audio(out_path):
    """Generate ambient synth pad + subtle transitions using FFmpeg."""
    # Layered ambient pad: low drone + mid pad + high shimmer
    # Using FFmpeg's audio synthesis
    cmd = [
        "ffmpeg", "-y",
        # Layer 1: Deep bass drone (60Hz sine with slow vibrato)
        "-f", "lavfi", "-i",
        f"sine=frequency=60:duration={TOTAL_SECONDS},tremolo=f=0.3:d=0.4,volume=0.15",
        # Layer 2: Mid-range warm pad (mixed sine waves)
        "-f", "lavfi", "-i",
        f"sine=frequency=174:duration={TOTAL_SECONDS},tremolo=f=0.5:d=0.3,volume=0.08",
        # Layer 3: Higher harmonic
        "-f", "lavfi", "-i",
        f"sine=frequency=261:duration={TOTAL_SECONDS},tremolo=f=0.7:d=0.2,volume=0.05",
        # Layer 4: Soft noise texture
        "-f", "lavfi", "-i",
        f"anoisesrc=d={TOTAL_SECONDS}:c=pink:a=0.02",
        # Mix all layers together with fade in/out
        "-filter_complex",
        "[0:a][1:a][2:a][3:a]amix=inputs=4:duration=longest,"
        f"afade=t=in:st=0:d=2,afade=t=out:st={TOTAL_SECONDS - 2}:d=2,"
        "equalizer=f=200:t=q:w=2:g=3,"
        "lowpass=f=4000,"
        "volume=1.5",
        "-ar", "44100", "-ac", "2",
        "-c:a", "aac", "-b:a", "128k",
        str(out_path)
    ]
    subprocess.run(cmd, capture_output=True)


# ── Main render pipeline ──────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("AirGuard AI — Launch Video Renderer")
    print("=" * 60)

    # Step 1: Render all frames
    print(f"\n▸ Rendering {TOTAL_FRAMES} frames at {W}×{H} @ {FPS}fps...")
    for i in range(TOTAL_FRAMES):
        frame_img = render_frame(i)
        frame_path = FRAME_DIR / f"frame_{i:05d}.png"
        frame_img.save(frame_path, "PNG")
        if (i + 1) % 30 == 0 or i == 0:
            pct = (i + 1) / TOTAL_FRAMES * 100
            print(f"  Frame {i + 1}/{TOTAL_FRAMES} ({pct:.0f}%)")

    print("\n▸ Generating ambient audio track...")
    audio_path = OUT / "_audio.m4a"
    generate_audio(audio_path)

    # Step 2: Encode video with FFmpeg
    print("\n▸ Encoding final video with FFmpeg...")
    video_out = OUT / "airguard-launch.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", str(FRAME_DIR / "frame_%05d.png"),
        "-i", str(audio_path),
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-movflags", "+faststart",
        str(video_out)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FFmpeg error:\n{result.stderr[-1000:]}")
        sys.exit(1)

    # Step 3: Extract poster frame (frame at 3s)
    print("\n▸ Extracting poster frame...")
    poster_path = OUT / "airguard-poster.jpg"
    poster_frame = render_frame(3 * FPS)
    poster_frame.save(poster_path, "JPEG", quality=92)

    # Step 4: Create teaser GIF (5-second loop from highlights)
    print("\n▸ Creating teaser GIF...")
    gif_path = OUT / "airguard-teaser.gif"
    # Sample frames: intro climax, dashboard, devices, model lab, outro
    gif_frames = []
    sample_times = [2.5, 4.0, 7.5, 12.5, 17.5, 22.5, 27.0]
    for st in sample_times:
        f = render_frame(int(st * FPS))
        # Downscale for GIF
        f = f.resize((960, 540), Image.LANCZOS)
        gif_frames.append(f)
    # Also add smooth transition frames between samples
    all_gif_frames = []
    for i, f in enumerate(gif_frames):
        all_gif_frames.append(f)
        if i < len(gif_frames) - 1:
            # Add 2 blend frames
            for bt in [0.33, 0.66]:
                blended = crossfade(f, gif_frames[i + 1], bt)
                all_gif_frames.append(blended)

    all_gif_frames[0].save(
        gif_path,
        save_all=True,
        append_images=all_gif_frames[1:],
        duration=400,  # 400ms per frame
        loop=0,
        optimize=True
    )

    # Step 5: Social share copy
    print("\n▸ Writing social share copy...")
    share_path = OUT / "share-copy.txt"
    share_path.write_text(
        "🌬️ Introducing AirGuard AI — an open-source, AI-powered environmental\n"
        "monitoring system that connects your air-quality sensors, detects anomalies,\n"
        "predicts molecular odors, and automates smart-home responses.\n"
        "\n"
        "Built with Python, Next.js, FastAPI, OpenPOM, and real ML evaluation pipelines.\n"
        "\n"
        "🔗 github.com/PRAFULREDDYM/AirGuard-AI\n"
        "#AirGuardAI #OpenSource #AirQuality #MachineLearning #IoT #Python #NextJS\n"
    )

    # Cleanup temp frames
    print("\n▸ Cleaning up temporary frames...")
    shutil.rmtree(FRAME_DIR)
    if audio_path.exists():
        audio_path.unlink()

    # Report
    print("\n" + "=" * 60)
    print("✅ LAUNCH VIDEO RENDERED SUCCESSFULLY")
    print("=" * 60)
    for f in ["airguard-launch.mp4", "airguard-poster.jpg",
              "airguard-teaser.gif", "share-copy.txt"]:
        p = OUT / f
        if p.exists():
            size_mb = p.stat().st_size / (1024 * 1024)
            print(f"  {f}: {size_mb:.1f} MB")
        else:
            print(f"  {f}: MISSING")
    print()


if __name__ == "__main__":
    main()

