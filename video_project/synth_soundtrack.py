#!/usr/bin/env python3
"""
AirGuard AI — Cinematic Soundtrack & SFX Synthesizer
Generates an original 35.0s master stereo WAV at 48kHz using numpy.
Features:
- 116 BPM electronic tech groove
- Synthesized analog instruments (FM keys, round bass, supersaw pads, drums)
- Synchronized cinematic sound design (sub impact, risers, whooshes, UI blips, chimes)
- High dynamic range and polished mixing
"""

import math
import os
import wave
from pathlib import Path
import numpy as np

SR = 48000
DURATION = 35.0
TOTAL_SAMPLES = int(SR * DURATION)
BPM = 116.0
BEAT_SEC = 60.0 / BPM
BAR_SEC = BEAT_SEC * 4.0

def midi_to_freq(m):
    return 440.0 * (2.0 ** ((m - 69.0) / 12.0))

class AudioTrack:
    def __init__(self):
        self.left = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
        self.right = np.zeros(TOTAL_SAMPLES, dtype=np.float32)

    def add_stereo(self, l_arr, r_arr, start_sec, gain=1.0):
        start_idx = int(start_sec * SR)
        n = len(l_arr)
        if start_idx >= TOTAL_SAMPLES or n == 0:
            return
        end_idx = min(TOTAL_SAMPLES, start_idx + n)
        slice_len = end_idx - start_idx
        self.left[start_idx:end_idx] += l_arr[:slice_len] * gain
        self.right[start_idx:end_idx] += r_arr[:slice_len] * gain

    def add_mono(self, arr, start_sec, gain=1.0, pan=0.0):
        # pan: -1.0 (left) to 1.0 (right)
        l_gain = gain * math.cos((pan + 1.0) * math.pi / 4.0) * math.sqrt(2)
        r_gain = gain * math.sin((pan + 1.0) * math.pi / 4.0) * math.sqrt(2)
        self.add_stereo(arr * l_gain, arr * r_gain, start_sec)

# ── Voice synthesis generators ─────────────────────────────────────────────

def synth_sub_impact(dur=2.5, start_freq=120.0, end_freq=35.0):
    """Cinematic sub-bass boom / impact with exponential pitch drop."""
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    # Pitch curve
    freq = end_freq + (start_freq - end_freq) * np.exp(-t * 6.0)
    phase = 2.0 * np.pi * np.cumsum(freq) / SR
    sub = np.sin(phase) * np.exp(-t * 2.2)
    # Add subtle saturation
    sub = np.tanh(sub * 2.0)
    # Add initial click transient
    click = np.random.randn(n) * np.exp(-t * 120.0) * 0.4
    return (sub + click).astype(np.float32)

def synth_kick(dur=0.4, tone=55.0):
    """Tight electronic kick drum."""
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    freq = tone + 130.0 * np.exp(-t * 40.0)
    phase = 2.0 * np.pi * np.cumsum(freq) / SR
    body = np.sin(phase) * np.exp(-t * 12.0)
    click = np.random.randn(n) * np.exp(-t * 300.0) * 0.2
    return np.tanh((body + click) * 1.5).astype(np.float32)

def synth_snare(dur=0.35):
    """Crisp electronic snare."""
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    noise = np.random.randn(n) * np.exp(-t * 18.0)
    tone = np.sin(2.0 * np.pi * 180.0 * t) * np.exp(-t * 28.0) * 0.6
    return (noise * 0.7 + tone).astype(np.float32)

def synth_hihat(dur=0.08, open_hat=False):
    """High-passed noise hat."""
    d = 0.3 if open_hat else 0.08
    n = int(SR * d)
    t = np.linspace(0, d, n, endpoint=False)
    decay = 10.0 if open_hat else 65.0
    noise = np.random.randn(n) * np.exp(-t * decay)
    # High-pass filter via diff
    hp = np.diff(noise, prepend=0)
    return hp.astype(np.float32) * 0.6

def synth_bass_note(midi, dur=0.4):
    """Warm analog saw/sine bass note."""
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    f = midi_to_freq(midi)
    sine = np.sin(2.0 * np.pi * f * t)
    sub = np.sin(np.pi * f * t) * 0.4
    saw = (2.0 * (f * t % 1.0) - 1.0) * 0.3
    env = np.minimum(t / 0.008, 1.0) * np.exp(-t * 3.5)
    raw = (sine + sub + saw) * env
    return np.tanh(raw * 1.4).astype(np.float32)

def synth_pad_chord(midis, dur=2.5, attack=0.3, release=0.5):
    """Lush supersaw chord pad."""
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    left = np.zeros(n, dtype=np.float32)
    right = np.zeros(n, dtype=np.float32)
    
    # Envelope
    env = np.ones(n, dtype=np.float32)
    att_samples = int(SR * attack)
    rel_samples = int(SR * release)
    if att_samples > 0:
        env[:att_samples] = np.linspace(0, 1, att_samples)
    if rel_samples > 0:
        env[-rel_samples:] = np.linspace(1, 0, rel_samples)

    for m in midis:
        f = midi_to_freq(m)
        # Detuned oscillators for rich width
        detunes = [-0.006, 0.0, 0.006]
        for idx, d in enumerate(detunes):
            f_detuned = f * (1.0 + d)
            osc = np.sin(2.0 * np.pi * f_detuned * t) + 0.3 * np.sin(4.0 * np.pi * f_detuned * t)
            pan = (idx - 1) * 0.6
            left += osc * (1.0 - pan) * 0.5
            right += osc * (1.0 + pan) * 0.5

    scale = 0.25 / len(midis)
    return (left * env * scale, right * env * scale)

def synth_pluck(midi, dur=0.5):
    """Crisp FM bell/pluck."""
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    f = midi_to_freq(midi)
    mod = np.sin(2.0 * np.pi * f * 2.0 * t) * np.exp(-t * 15.0) * 2.0
    carrier = np.sin(2.0 * np.pi * f * t + mod) * np.exp(-t * 6.0)
    return carrier.astype(np.float32)

def synth_whoosh(dur=0.45, rise=True):
    """Cinematic noise transition whoosh."""
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    noise = np.random.randn(n)
    if rise:
        env = (t / dur) ** 2.0 * np.sin(np.pi * t / dur)
    else:
        env = (1.0 - t / dur) ** 2.0 * np.sin(np.pi * t / dur)
    # Simple low/bandpass shaping
    lp = np.convolve(noise, np.ones(12) / 12.0, mode='same')
    return (lp * env * 0.8).astype(np.float32)

def synth_riser(dur=2.0):
    """Tension build riser leading into scene transitions."""
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    freq = 150.0 + 3500.0 * (t / dur) ** 2.5
    phase = 2.0 * np.pi * np.cumsum(freq) / SR
    tone = np.sin(phase) * (t / dur) ** 1.8
    noise = np.random.randn(n) * (t / dur) ** 2.0 * 0.3
    return (tone + noise).astype(np.float32) * 0.5

def synth_chime_chord(midis, dur=2.0):
    """Harmonic chime for logo resolve and UI milestones."""
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    out = np.zeros(n, dtype=np.float32)
    for m in midis:
        f = midi_to_freq(m)
        osc = np.sin(2.0 * np.pi * f * t) * np.exp(-t * 2.5)
        harm = np.sin(4.0 * np.pi * f * t) * np.exp(-t * 4.0) * 0.3
        out += osc + harm
    return (out * (0.3 / len(midis))).astype(np.float32)

# ── Master Arrangement ─────────────────────────────────────────────────────

def generate_soundtrack():
    track = AudioTrack()

    # 1. Chords progression (F minor -> Ab major -> Eb major -> Bb sus4/add9)
    # Keys in MIDI numbers:
    # Fm9:  [53(F3), 60(C4), 63(Eb4), 65(F4), 68(Ab4), 72(C5)]
    # AbM7: [56(Ab3), 60(C4), 63(Eb4), 67(G4), 72(C5)]
    # Ebadd9: [51(Eb3), 58(Bb3), 63(Eb4), 65(F4), 70(Bb4)]
    # Bbsus: [46(Bb2), 58(Bb3), 63(Eb4), 65(F4), 70(Bb4)]
    # Resolving Finale: F major add9 [53(F3), 57(A3), 60(C4), 65(F4), 67(G4), 72(C5)]

    chords = [
        ([53, 60, 63, 68, 72], 0.0, 4.14),     # 0-4s: Dark intro Fm
        ([53, 60, 65, 68], 4.14, 4.14),        # 4-8s: Monitoring Fm
        ([56, 60, 63, 67], 8.28, 4.14),        # 8-12s: Devices Ab
        ([51, 58, 63, 65, 70], 12.42, 4.14),   # 12-16s: Intelligence Eb
        ([53, 60, 65, 68], 16.56, 4.14),       # 16-20s: Models Fm
        ([46, 58, 63, 65], 20.70, 4.14),       # 20-24s: Automation tension Bb
        ([53, 60, 65, 68], 24.84, 2.07),       # 24-27s: Escalation Fm
        ([56, 60, 63, 67], 26.91, 2.07),       # 27-29s: Rapid montage Ab
        ([51, 58, 65, 70], 28.98, 2.07),       # 29-31s: Montage climax Eb
        ([53, 57, 60, 65, 67, 72], 31.05, 3.95)# 31-35s: Outro resolution F major!
    ]

    print("  Synthesizing harmonic pads...")
    for midis, start_t, dur in chords:
        pl, pr = synth_pad_chord(midis, dur=dur + 0.5, attack=0.2, release=0.4)
        track.add_stereo(pl, pr, start_t, gain=0.65)

    # 2. Bassline
    print("  Synthesizing analog bassline...")
    bass_patterns = [
        # (midi, start_sec, dur)
        # Intro sub swells
        (41, 0.1, 3.5),
        # Scene 1 Dashboard groove
        (41, 4.14, 0.45), (41, 4.66, 0.45), (44, 5.17, 0.45), (46, 5.69, 0.45),
        (41, 6.21, 0.45), (41, 6.73, 0.45), (39, 7.24, 0.45), (36, 7.76, 0.45),
        # Scene 2 Devices
        (44, 8.28, 0.45), (44, 8.79, 0.45), (48, 9.31, 0.45), (46, 9.83, 0.45),
        (44, 10.35, 0.45), (44, 10.86, 0.45), (46, 11.38, 0.45), (48, 11.90, 0.45),
        # Scene 3 AI Model Lab
        (39, 12.42, 0.45), (39, 12.93, 0.45), (43, 13.45, 0.45), (44, 13.97, 0.45),
        (41, 14.48, 0.45), (41, 15.00, 0.45), (44, 15.52, 0.45), (46, 16.04, 0.45),
        (41, 16.56, 0.45), (41, 17.07, 0.45), (39, 17.59, 0.45), (36, 18.11, 0.45),
        # Scene 4 Automation
        (34, 20.70, 0.45), (34, 21.21, 0.45), (38, 21.73, 0.45), (39, 22.25, 0.45),
        (41, 22.76, 0.45), (41, 23.28, 0.45), (44, 23.80, 0.45), (46, 24.32, 0.45),
        # Scene 5 Montage (double-pulse drive)
        (41, 26.91, 0.25), (41, 27.17, 0.25), (41, 27.43, 0.25), (44, 27.69, 0.25),
        (44, 27.94, 0.25), (46, 28.20, 0.25), (48, 28.46, 0.25), (51, 28.72, 0.25),
        (39, 28.98, 0.25), (39, 29.24, 0.25), (41, 29.50, 0.25), (43, 29.76, 0.25),
        (44, 30.01, 0.25), (46, 30.27, 0.25), (48, 30.53, 0.25), (50, 30.79, 0.25),
        # Outro root
        (41, 31.05, 3.5),
    ]
    for midi, st, dur in bass_patterns:
        note = synth_bass_note(midi, dur)
        track.add_mono(note, st, gain=0.7)

    # 3. Drums & Percussion
    print("  Synthesizing punchy rhythmic drums...")
    # Kicks on beats (starts at bar 2 = 4.14s up to 31.0s)
    cur_t = 4.14
    while cur_t < 31.0:
        # Standard four-on-the-floor or syncopated
        track.add_mono(synth_kick(0.35), cur_t, gain=0.85)
        # Add 16th note bounce during montage
        if cur_t >= 26.91:
            track.add_mono(synth_kick(0.2), cur_t + BEAT_SEC * 0.5, gain=0.55)
        cur_t += BEAT_SEC

    # Snares on beats 2 and 4 (starting at 8.28s)
    cur_t = 8.28 + BEAT_SEC
    while cur_t < 31.0:
        track.add_mono(synth_snare(0.3), cur_t, gain=0.65)
        cur_t += BEAT_SEC * 2.0

    # Hi-hats (8th notes from 4.14s, 16th notes in montage)
    cur_t = 4.14
    while cur_t < 31.0:
        track.add_mono(synth_hihat(0.06), cur_t, gain=0.35, pan=-0.3)
        if cur_t >= 8.28:
            track.add_mono(synth_hihat(0.06), cur_t + BEAT_SEC * 0.5, gain=0.25, pan=0.3)
        cur_t += BEAT_SEC

    # 4. Pluck Arpeggio / Melodic accents
    print("  Synthesizing melodic plucks and motifs...")
    arp_notes = [
        # (midi, time)
        (72, 8.28), (75, 8.54), (77, 8.80), (75, 9.06),
        (72, 9.31), (75, 9.57), (80, 9.83), (77, 10.09),
        (72, 12.42), (75, 12.68), (79, 12.94), (77, 13.20),
        (75, 13.45), (72, 13.71), (70, 13.97), (68, 14.23),
        # AI Model lab high tech pulses
        (84, 14.48), (87, 14.74), (89, 15.00), (84, 15.26),
        (87, 16.56), (89, 16.82), (91, 17.07), (87, 17.33),
        # Montage energetic stabs
        (72, 26.91), (75, 27.17), (77, 27.43), (80, 27.69),
        (77, 27.94), (80, 28.20), (84, 28.46), (87, 28.72),
        (84, 28.98), (87, 29.24), (89, 29.50), (92, 29.76),
    ]
    for midi, st in arp_notes:
        p = synth_pluck(midi, 0.4)
        track.add_mono(p, st, gain=0.45, pan=0.2)

    # 5. Cinematic Sound Design (SFX)
    print("  Synthesizing cinematic SFX (impacts, whooshes, chimes, risers)...")
    # Opening: Sub impact + sweep
    track.add_mono(synth_sub_impact(3.0, 140.0, 38.0), 0.05, gain=0.95)
    track.add_mono(synth_whoosh(0.6, rise=True), 1.8, gain=0.5, pan=-0.4)
    track.add_mono(synth_chime_chord([72, 77, 84], 2.0), 2.2, gain=0.6, pan=0.0)

    # Transition to Dashboard (4.14s)
    track.add_mono(synth_whoosh(0.5, rise=False), 3.9, gain=0.55, pan=0.3)
    # UI tick when PM2.5 metric numbers rise (5.5s)
    track.add_mono(synth_pluck(84, 0.2), 5.5, gain=0.35, pan=-0.2)
    track.add_mono(synth_pluck(88, 0.2), 5.7, gain=0.35, pan=0.2)

    # Transition to Devices (8.28s)
    track.add_mono(synth_whoosh(0.5, rise=True), 8.0, gain=0.5)
    track.add_mono(synth_pluck(77, 0.25), 9.5, gain=0.4, pan=-0.3) # device connected node
    track.add_mono(synth_pluck(81, 0.25), 10.8, gain=0.4, pan=0.3) # purifier paired

    # Transition to AI Model Lab (14.48s)
    track.add_mono(synth_whoosh(0.55, rise=False), 14.2, gain=0.55)

    # Transition to Automation (20.70s)
    track.add_mono(synth_riser(1.8), 19.0, gain=0.5)
    # Alert triggered chime
    track.add_mono(synth_chime_chord([65, 71, 77], 1.5), 21.0, gain=0.65) # alert warning
    track.add_mono(synth_pluck(89, 0.3), 23.5, gain=0.45) # notification slide

    # Pre-Montage Riser (25.0s -> 26.91s)
    track.add_mono(synth_riser(1.9), 25.0, gain=0.65)

    # Rapid Montage Cuts Whooshes
    track.add_mono(synth_whoosh(0.3, rise=False), 26.91, gain=0.5, pan=-0.4)
    track.add_mono(synth_whoosh(0.3, rise=False), 27.94, gain=0.5, pan=0.4)
    track.add_mono(synth_whoosh(0.3, rise=False), 28.98, gain=0.5, pan=-0.3)
    track.add_mono(synth_whoosh(0.3, rise=False), 30.01, gain=0.5, pan=0.3)

    # Outro Climax Riser & Final Logo Impact (31.05s)
    track.add_mono(synth_sub_impact(3.5, 160.0, 32.0), 31.05, gain=1.0)
    # Grand resolving outro chord
    track.add_mono(synth_chime_chord([53, 57, 60, 65, 67, 72, 77], 3.8), 31.1, gain=0.85)

    # 6. Master Limiter & Normalization
    print("  Applying mastering limiter and headroom...")
    max_peak = max(np.max(np.abs(track.left)), np.max(np.abs(track.right)))
    if max_peak > 0:
        # Normalize to peak -0.5 dBFS (~0.94)
        target_peak = 0.94
        scale = target_peak / max_peak
        track.left *= scale
        track.right *= scale

    # Smooth fade out at the very end (34.5 to 35.0s)
    fade_len = int(0.5 * SR)
    fade_curve = np.linspace(1.0, 0.0, fade_len)
    track.left[-fade_len:] *= fade_curve
    track.right[-fade_len:] *= fade_curve

    return track

def save_wav(track, out_path):
    print(f"  Writing master WAV to {out_path}...")
    l_int16 = np.clip(track.left * 32767.0, -32768, 32767).astype(np.int16)
    r_int16 = np.clip(track.right * 32767.0, -32768, 32767).astype(np.int16)
    # Interleave stereo
    stereo_int16 = np.empty((len(l_int16) * 2,), dtype=np.int16)
    stereo_int16[0::2] = l_int16
    stereo_int16[1::2] = r_int16

    with wave.open(str(out_path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(stereo_int16.tobytes())

def main():
    out_dir = Path("/Users/prafulreddy/Desktop/AirGuard AI/video_project")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_wav = out_dir / "soundtrack_master.wav"
    print("=" * 60)
    print("AirGuard AI — Soundtrack & SFX Engine")
    print("=" * 60)
    track = generate_soundtrack()
    save_wav(track, out_wav)
    print(f"✅ Generated {DURATION}s stereo master at {out_wav}")

if __name__ == "__main__":
    main()
