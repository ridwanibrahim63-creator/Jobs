#!/usr/bin/env python3
"""Original score + sound design for the Iceland film, synthesised from scratch.

No samples, no third-party music: every sound is generated here with numpy, so the
soundtrack is free to publish. 100 BPM, D minor, 58 beats (34.8 s) — the picture is
cut on this grid (see edit.py).

    python3 score.py   ->  build/score.wav (48 kHz stereo)
"""
import os, wave
import numpy as np

SR = 48000
BEAT = 0.6
DUR = 58 * BEAT + 1.0
N = int(DUR * SR)
rng = np.random.default_rng(7)
HERE = os.path.dirname(os.path.abspath(__file__))


def t_axis(d):
    return np.arange(int(d * SR)) / SR


def place(mix, sig, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    if i >= N:
        return
    sig = sig[: N - i]
    l = np.cos((pan + 1) * np.pi / 4); r = np.sin((pan + 1) * np.pi / 4)
    mix[0, i:i + len(sig)] += sig * gain * l * 1.414
    mix[1, i:i + len(sig)] += sig * gain * r * 1.414


def band_noise(d, lo, hi, slope=0.0):
    """Noise shaped in the frequency domain (band-limited, optional 1/f^slope tilt)."""
    n = int(d * SR)
    spec = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    g = 1 / (1 + (lo / np.maximum(f, 1)) ** 4) / (1 + (f / hi) ** 4)
    if slope:
        g = g / np.maximum(f, 20) ** slope
    x = np.fft.irfft(spec * g, n)
    return x / (np.abs(x).max() + 1e-9)


def env(d, a, r, curve=1.0):
    t = t_axis(d)
    e = np.minimum(t / max(a, 1e-4), 1) * np.minimum((d - t) / max(r, 1e-4), 1)
    return np.clip(e, 0, 1) ** curve


def note(m):
    return 440 * 2 ** ((m - 69) / 12)


def pad(midi, d, bright=0.5):
    """Warm string-like pad: detuned additive saws with a slow swell."""
    t = t_axis(d); out = np.zeros_like(t)
    for m in midi:
        f = note(m)
        for det in (-0.07, 0.0, 0.06):
            ff = f * 2 ** (det / 12); ph = rng.uniform(0, 6.28)
            for h in range(1, 9):
                amp = 1 / h ** (2.2 - bright)
                out += amp * np.sin(2 * np.pi * ff * h * t + ph * h)
    return out / np.abs(out).max() * env(d, d * .35, d * .4)


def keys(m, d=2.6, vel=1.0):
    """Felt-piano-ish pluck."""
    t = t_axis(d); f = note(m); out = np.zeros_like(t)
    for h, a in enumerate((1, .5, .28, .12, .06, .03), start=1):
        out += a * np.sin(2 * np.pi * f * h * (1 + .0004 * h * h) * t) * np.exp(-t * (1.6 + h * 1.1))
    return out * vel * np.minimum(t / .006, 1)


def boom(d=2.2, f0=95, f1=32, click=.4):
    t = t_axis(d)
    f = f1 + (f0 - f1) * np.exp(-t * 9)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.4)
    thump = band_noise(d, 30, 220) * np.exp(-t * 14) * click
    return body + thump


def drum(d=.7, f0=120, f1=52):
    t = t_axis(d)
    f = f1 + (f0 - f1) * np.exp(-t * 28)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7.5) + \
        band_noise(d, 80, 900) * np.exp(-t * 30) * .35


def tick(d=.12):
    return band_noise(d, 5000, 11000) * np.exp(-t_axis(d) * 60)


def riser(d):
    t = t_axis(d); out = np.zeros_like(t)
    for k, (lo, hi) in enumerate(((150, 500), (400, 1400), (1200, 4000), (3500, 9000))):
        out += band_noise(d, lo, hi) * np.clip((t / d - k * .18) / (1 - k * .18), 0, 1) ** 2.5
    tone = np.sin(2 * np.pi * np.cumsum(110 * 2 ** (t / d * 1.5)) / SR) * (t / d) ** 3 * .5
    return (out / np.abs(out).max() + tone) * (t / d) ** 1.5


def whoosh(d=.7):
    t = t_axis(d)
    return band_noise(d, 300, 5000) * np.exp(-((t - d * .55) / (d * .2)) ** 2)


def reverb(x, secs=3.2, wet=.3):
    n = int(secs * SR); t = np.arange(n) / SR
    out = np.zeros_like(x)
    for c in range(2):
        ir = rng.standard_normal(n) * np.exp(-t * 6.9 / secs) * np.minimum(t / .012, 1)
        m = x.shape[1] + n
        y = np.fft.irfft(np.fft.rfft(x[c], m) * np.fft.rfft(ir, m), m)[: x.shape[1]]
        out[c] = y
    out /= np.abs(out).max() + 1e-9
    return x + out * wet * np.abs(x).max()


def build():
    music = np.zeros((2, N)); dry = np.zeros((2, N)); amb = np.zeros((2, N))
    bar = 4 * BEAT
    # ---- harmony: Dm - Bb - F - C, one chord per bar, brightening through the film
    chords = [(50, 57, 62, 65), (46, 53, 58, 62), (53, 57, 60, 65), (48, 55, 60, 64)]
    roots = [38, 34, 41, 36]
    for b in range(16):
        at = b * bar
        if at >= 58 * BEAT:
            break
        level = (.24 if b < 1 else .22 if b < 5 else .3 if b < 10 else .46)
        bright = .2 + .06 * b
        ch = chords[b % 4]
        if b >= 10:
            ch = ch + (ch[1] + 12, ch[3] + 12)
        place(music, pad(ch, bar * 1.6, min(bright, 1.0)), at - .25 if b else 0, level)
        if b >= 2:                                           # sub bass from the journey on
            t = t_axis(bar * 1.05)
            sub = np.sin(2 * np.pi * note(roots[b % 4]) * t) * env(bar * 1.05, .08, .5)
            place(dry, sub, at, .2 if b < 10 else .34)
    # ---- motif (felt piano), sparse at first, doubled an octave up in the payoff
    motif = [(0, 69), (1.5, 65), (2, 62), (3, 64),   (4, 65), (5.5, 62), (6, 58), (7, 60),
             (8, 69), (9.5, 72), (10, 65), (11, 67), (12, 64), (13.5, 67), (14, 60), (15, 62)]
    for rep, (start_bar, vel, octave) in enumerate(((2, .32, False), (6, .42, False),
                                                    (10, .6, True), (13.25, .4, False))):
        for bt, m in motif:
            at = start_bar * bar + bt * BEAT
            if at > 57 * BEAT or (rep == 3 and bt > 5):
                continue
            place(music, keys(m, vel=vel), at, .5, pan=-.15)
            if octave:
                place(music, keys(m + 12, vel=vel * .55), at, .5, pan=.25)
    # ---- pulse: light from the title on, builds to 23.6, lands at 24 s
    for b in range(8, 40):
        at = b * BEAT
        if at >= 23.4:
            break
        g = .2 + .42 * (b - 8) / 32
        if b % 2 == 0:
            place(dry, drum(), at, g * .8)
        if b % 4 == 3 and b > 18:
            place(dry, drum(.5, 150, 70), at + .5 * BEAT, g * .45)
        for sub in (0, .5):
            place(dry, tick(), at + sub * BEAT, g * .16, pan=.4 if sub else -.4)
    for b in range(40, 53):                                  # payoff groove
        at = b * BEAT; k = b - 40
        fade = 1.0 if at < 30.0 else .55
        if k % 4 in (0, 2):
            place(dry, drum(.9, 110, 46), at, .78 * fade)
        if k % 8 in (3, 7):
            place(dry, drum(.5, 150, 70), at + .5 * BEAT, .4 * fade)
        for sub in (0, .5):
            place(dry, tick(), at + sub * BEAT, .1 * fade, pan=.4 if sub else -.4)
    # ---- impacts, risers, whooshes: tied to the picture cuts
    place(dry, riser(2.4), 0.0, .4)                          # map + flash montage
    for i in range(9):                                       # one hit per 0.2 s flash
        place(dry, drum(.25, 190 + 14 * i, 90), .6 + i * .2, .34 + .03 * i, pan=(-.5, .5, 0)[i % 3])
        place(dry, tick(.08), .6 + i * .2, .2)
    place(dry, boom(2.6), 2.4, 1.0)                          # TITLE shot
    place(dry, tick(.1), 3.0, .3)
    place(dry, whoosh(.6), 4.5, .22, pan=-.3)
    place(dry, boom(1.8, 80, 36, .2), 4.8, .5)               # the trip starts
    place(dry, whoosh(.7), 11.0, .22, pan=.3)                # into the crater pull-out
    place(dry, boom(1.8, 80, 36, .2), 11.4, .5)
    place(dry, boom(1.6, 80, 36, .2), 19.2, .45)             # geothermal sun
    place(dry, whoosh(.8), 20.0, .22)
    place(dry, riser(2.6), 21.1, .5)                         # build into the drop
    place(dry, boom(3.4, 110, 28, .7), 24.0, 1.15)           # THE DROP
    place(dry, boom(2.4, 85, 32, .3), 27.6, .6)
    place(dry, whoosh(1.0), 31.2, .2)
    place(dry, boom(3.0, 70, 30, .15), 31.8, .5)             # final shot
    # ---- synthetic ambience: wind bed + water roar under the waterfall shots
    wind = band_noise(DUR, 180, 900, .5)
    lfo = .55 + .45 * np.sin(2 * np.pi * .13 * t_axis(DUR) + 1) * np.sin(2 * np.pi * .05 * t_axis(DUR))
    w2 = band_noise(DUR, 180, 900, .5)
    amb[0] += wind[:N] * lfo[:N] * .05; amb[1] += w2[:N] * lfo[:N] * .05
    t = np.arange(N) / SR

    def window(a, b, ramp=.5):
        return np.clip((t - a) / ramp, 0, 1) * np.clip((b - t) / ramp, 0, 1)
    water = band_noise(DUR, 90, 6000, .55)[:N]; water2 = band_noise(DUR, 90, 6000, .55)[:N]
    wenv = window(13.2, 14.4, .15) * .4 + window(20.4, 24.0, .8) * .42 + window(24.0, 30.2, .2) * .5
    amb[0] += water * wenv * .16; amb[1] += water2 * wenv * .16
    road = band_noise(DUR, 40, 260, .3)[:N]
    amb += road * window(4.8, 6.1, .15) * .12
    # ---- mix
    mix = reverb(music, 3.4, .5) + reverb(dry, 1.8, .14) + amb
    gap = 1 - .93 * window(23.62, 24.0, .04)                 # a held breath before the drop
    mix *= gap
    mix *= np.clip((58 * BEAT + .1 - t) / 2.6, 0, 1) ** 1.6  # long, clean tail to silence
    mix *= np.clip(t / .03, 0, 1)
    mix = mix / np.abs(mix).max()
    mix = np.tanh(mix * 2.1) / np.tanh(2.1)                  # glue + soft limiting
    mix *= 10 ** (-1.0 / 20)
    return mix


if __name__ == "__main__":
    mix = build()
    os.makedirs(os.path.join(HERE, "build"), exist_ok=True)
    out = os.path.join(HERE, "build", "score.wav")
    with wave.open(out, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix.T * 32767).astype("<i2").tobytes())
    print("wrote", out, f"{mix.shape[1] / SR:.2f}s")
