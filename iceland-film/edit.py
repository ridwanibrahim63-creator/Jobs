#!/usr/bin/env python3
"""ICELAND — Golden Circle, winter. Cinematic 9:16 edit.

Reproducible renderer: every creative decision (shot order, in/out points,
speed ramps, reframing, grade, transitions, title) lives in SHOTS below.

    ICELAND_SRC=/path/to/footage python3 edit.py            # full render
    ICELAND_SRC=... python3 edit.py --preview               # half-res, fast
    ICELAND_SRC=... python3 edit.py --only 14,15            # re-render shots

Source files are only ever read. Needs: ffmpeg, numpy, Pillow.
"""
import glob, os, subprocess, sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.environ.get("ICELAND_SRC", os.path.join(HERE, "footage"))
BUILD = os.path.join(HERE, "build")
OUT = os.path.join(HERE, "output")
FPS = 30
BEAT = 18                      # frames per beat -> 100 BPM
PREVIEW = "--preview" in sys.argv
W, H = (540, 960) if PREVIEW else (1080, 1920)


# ---------------------------------------------------------------- timeline
# beats : length on the 100 BPM grid
# time  : [(u, source_seconds)] u=0..1 through the shot -> speed ramps
# crop  : [(source_seconds, cx, cy, zoom)] reframing keyframes (fractions of frame)
# fix   : per-shot correction before the film look (exp, con, temp, sat)
def flash(i, src, t, **kw):
    """One 0.2 s frame-burst for the opening montage (three per beat)."""
    return dict(id=100 + i, name="flash-" + src, src=src, beats=1 / 3,
                time=[(0, t), (1, t + .3)], crop=[(0, kw.pop("cx", .5), .5, kw.pop("zoom", 1.06))] * 1,
                fix=kw.pop("fix", {}), **kw)


def photo(i, name, src, crop, fix=None, beats=2, **kw):
    """A still with keyframed movement; crop keys run 0..1 through the shot."""
    return dict(id=i, name=name, src=src, beats=beats, still=True, time=[(0, 0), (1, 1)],
                crop=crop, fix=fix or {}, **kw)


# The 21 top-ranked shots (docs/05-shot-ranking.md). Hard cuts on the beat throughout.
SHOTS = [
 # ---- HOOK: map, then a strobe of what is coming (ref A / C)
 dict(id=1,  name="map-zoom",        src="RPReplay", beats=1, vf="transpose=1",
      time=[(0, .85), (1, 1.5)], crop=[(0, .5, .5, 1)], fix=dict(exp=.9, sat=.85)),
 flash(1, "DJI_0127", 1.0, cx=.52, fix=dict(exp=.93, con=1.06)),
 flash(2, "IMG_2687_2", 5.2, fix=dict(sat=.88)),
 flash(3, "copy_19AB", 7.0, cx=.53),
 flash(4, "DJI_0123", 46.0, cx=.58, fix=dict(con=1.06)),
 flash(5, "IMG_2701", 0, still=True, fix=dict(sat=.88)),
 flash(6, "IMG_2014", 0, still=True, cx=.56, fix=dict(sat=.92)),
 flash(7, "IMG_2600", 5.0),
 flash(8, "DJI_0118", 58.2, cx=.64),
 flash(9, "DJI_0129", 8.0, cx=.51, fix=dict(con=1.05)),
 # ---- HERO + TITLE: type holds while the picture cuts beneath it (ref A / B)
 dict(id=4,  name="road-hyperlapse", src="DJI_0103", beats=4,
      time=[(0, 12), (.3, 21), (.6, 27), (1, 31)],
      crop=[(12, .50, .5, 1), (33.5, .52, .5, 1)], fix=dict(con=1.04), interp=2),
 # ---- THE TRIP: two beats a shot, a person in most of them (ref B)
 photo(34, "drone-setup", "DSCF9120", [(0, .5, .56, 1.0), (1, .52, .58, 1.1)], dict(con=1.03)),
 dict(id=5,  name="takeoff-reveal",  src="DJI_0118", beats=2,
      time=[(0, 1.0), (1, 3.6)],
      crop=[(0, .43, .5, 1), (1.5, .43, .5, 1), (3, .48, .5, 1), (5, .60, .5, 1)], fix={}),
 dict(id=18, name="car-follow",      src="DJI_0102", beats=3,
      time=[(0, 1.0), (1, 5.4)], crop=[(0, .58, .5, 1), (3.3, .62, .5, 1), (6.7, .69, .5, 1)],
      fix=dict(con=1.04)),
 photo(30, "watch-compass", "DSCF9166", [(0, .47, .52, 1.22), (1, .47, .52, 1.36)], dict(con=1.04)),
 # subject-locked match cut (ref D): arms open on the tundra -> arms wide on the glacier
 dict(id=9,  name="arms-open",       src="DJI_0123", beats=2,
      time=[(0, 11.7), (1, 12.9)],
      crop=[(11.7, .39, .5, 1), (12, .36, .5, 1), (12.6, .29, .5, 1), (12.9, .26, .5, 1)],
      fix=dict(exp=.86, sat=.82, temp=.03)),
 dict(id=24, name="glacier-arms",    src="IMG_2687_2", beats=2,
      time=[(0, 5.1), (1, 6.3)], crop=[(5.1, .5, .40, 1.55), (5.5, .5, .43, 1.3), (6.3, .5, .5, 1.0)],
      fix=dict(sat=.88)),
 photo(35, "snowmobile-convoy", "IMG_2014", [(0, .55, .5, 1.0), (1, .58, .49, 1.12)], dict(sat=.92)),
 dict(id=20, name="kerid-crater",    src="copy_19AB", beats=3,
      time=[(0, 4.0), (1, 8.4)], crop=[(0, .53, .5, 1)], fix=dict(con=1.04)),
 dict(id=21, name="seljalandsfoss",  src="IMG_2600", beats=2,
      time=[(0, 4.6), (1, 5.8)], crop=[(0, .5, .5, 1)], fix=dict(con=1.04)),
 # the friends beat: the film's emotional centre (ref C's group hold)
 photo(32, "huddle", "IMG_2701", [(0, .5, .5, 1.0), (1, .5, .5, 1.1)], dict(sat=.88)),
 photo(33, "crew-truck", "IMG_2707", [(0, .40, .5, 1.0), (1, .61, .5, 1.0)], dict(sat=.88)),
 # ---- GULLFOSS BUILD
 dict(id=10, name="gullfoss-reveal", src="DJI_0131", beats=3,
      time=[(0, 8.0), (.4, 11.8), (1, 15.0)],
      crop=[(5, .72, .5, 1), (9, .62, .5, 1), (12, .50, .5, 1), (15, .36, .5, 1), (16, .33, .5, 1)],
      fix=dict(con=1.05), interp=4),
 dict(id=2,  name="ice-curtain",     src="DJI_0127", beats=3,
      time=[(0, .4), (1, 2.9)], crop=[(0, .50, .5, 1), (5, .57, .5, 1)],
      fix=dict(exp=.93, con=1.06)),
 dict(id=13, name="canyon-glide",    src="DJI_0127", beats=2,
      time=[(0, 13.6), (1, 16.2)], crop=[(13.5, .62, .5, 1), (16.5, .66, .5, 1)],
      fix=dict(exp=.95, con=1.06), close_bars=13),      # letterbox close to black (ref A)
 # ---- PAYOFF: the one long hold
 dict(id=14, name="the-drop",        src="DJI_0123", beats=6,
      time=[(0, 42.4), (1, 46.0)],
      crop=[(41, .45, .5, 1), (43.5, .45, .5, 1), (46.5, .60, .5, 1), (47.6, .62, .5, 1)],
      fix=dict(con=1.06)),
 dict(id=15, name="gullfoss-sunset", src="DJI_0129", beats=4,
      time=[(0, 6), (1, 10.8)], crop=[(6, .50, .5, 1), (12, .53, .5, 1)],
      fix=dict(con=1.05, temp=.02)),
 dict(id=16, name="silhouette",      src="DJI_0118", beats=3,
      time=[(0, 57.2), (1, 59.0)],
      crop=[(57, .78, .5, 1), (58, .64, .5, 1), (59.2, .62, .5, 1)],
      fix=dict(temp=.02), to_white=6),
 dict(id=17, name="lake-sunset",     src="DJI_0104", beats=5,
      time=[(0, 16.8), (1, 19.0)], crop=[(0, .5, .5, 1)], track_sun=True,
      fix=dict(temp=.03), from_white=12, fade_out=10),
 photo(36, "aurora", "IMG_1900", [(0, .5, .46, 1.0), (1, .5, .44, 1.1)], dict(sat=1.05), beats=4,
       from_black=12, fade_out=40),
]
TITLE_IN, TITLE_OUT = 90, 180     # frames: on at beat 5, off (hard) two beats into the next shot


def nframes(s):
    return int(round(s["beats"] * BEAT))


TOTAL = sum(nframes(s) for s in SHOTS)


def src_path(key):
    hits = sorted(glob.glob(os.path.join(SRC, f"*{key}*.mp4"))) or \
        sorted(glob.glob(os.path.join(HERE, "stills", f"*{key}*.jpg")))
    if not hits:
        sys.exit(f"missing source clip *{key}*.mp4 in {SRC}")
    return hits[0]


def probe_fps(path):
    r = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", path]).decode().strip()
    a, b = r.split("/")
    return float(a) / float(b)


def decode(path, t0, t1, vf=None, interp=1):
    """Decode [t0,t1] to a uint8 array (n,h,w,3). Returns frames, fps, first-frame time.
    interp>1 synthesises in-between frames (motion-compensated) so hyperlapsed shots
    integrate into smooth motion blur instead of a stepped echo."""
    fps = probe_fps(path)
    f0 = max(0, int(np.floor(t0 * fps)) - 1)
    n = int(np.ceil((t1 - t0) * fps)) + 4
    chain = f"trim=start_frame={f0}:end_frame={f0 + n},setpts=PTS-STARTPTS"
    if vf:
        chain += "," + vf
    if interp > 1:
        chain += (f",minterpolate=fps={fps * interp:.5f}:mi_mode=mci:mc_mode=aobmc:"
                  "me_mode=bidir:vsbmc=1:scd=none")
    chain += ",format=rgb24"
    probe = subprocess.check_output(["ffmpeg", "-v", "error", "-i", path, "-vf", chain,
        "-frames:v", "1", "-f", "image2pipe", "-vcodec", "ppm", "-"])
    hdr = probe.split(b"\n", 3)
    w, h = map(int, hdr[1].split())
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", path, "-vf", chain,
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"])
    arr = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)
    return arr, fps * interp, f0 / fps


def interp_keys(keys, x):
    xs = [k[0] for k in keys]
    return [float(np.interp(x, xs, [k[i] for k in keys])) for i in range(1, len(keys[0]))]


def smooth_time(keys, u):
    """Monotone, eased speed-ramp curve through the keyframes."""
    us = np.array([k[0] for k in keys], float); ts = np.array([k[1] for k in keys], float)
    if len(keys) == 2:
        return float(np.interp(u, us, ts))
    # resample piecewise-linear curve and smooth it so speed changes glide
    g = np.linspace(0, 1, 401); y = np.interp(g, us, ts)
    k = np.hanning(81); k /= k.sum()
    ypad = np.concatenate([y[0] + (g[:40] - g[40]) * (y[1] - y[0]) / g[1],
                           y, y[-1] + (g[1:41]) * (y[-1] - y[-2]) / g[1]])
    ys = np.convolve(ypad, k, mode="valid")
    ys = y[0] + (ys - ys[0]) * (y[-1] - y[0]) / (ys[-1] - ys[0])
    return float(np.interp(u, g, ys))


def crop_resize(frame, cx, cy, zoom):
    h, w = frame.shape[:2]
    ch = h / zoom; cw = ch * W / H
    if cw > w:
        cw = w; ch = cw * H / W
    x0 = min(max(cx * w - cw / 2, 0), w - cw); y0 = min(max(cy * h - ch / 2, 0), h - ch)
    im = Image.fromarray(frame).resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch))
    return np.asarray(im, np.float32) / 255.0


# ---------------------------------------------------------------- colour
def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def neutral_fit(frame):
    """Flat, green-cast Fuji clips: per-channel affine that makes the darkest and
    brightest 4% neutral and stretches the flat tonal range. Fitted once per shot."""
    x = frame[::3, ::3].reshape(-1, 3).astype(np.float32) / 255.0
    l = x.mean(axis=1); lo, hi = np.percentile(l, [4, 96])
    d = x[l <= lo].mean(axis=0); b = x[l >= hi].mean(axis=0)
    gain = (.90 - .045) / (b - d)
    return gain.astype(np.float32), (.045 - d * gain).astype(np.float32)


def grade(img, fix):
    """Shot correction, then one shared film look so every camera sits together."""
    if "neutral" in fix:
        img = np.clip(img * fix["neutral"][0] + fix["neutral"][1], 0, 1)
    exp = fix.get("exp", 1.0); con = fix.get("con", 1.0)
    temp = fix.get("temp", 0.0); sat = fix.get("sat", 1.0)
    img = img * exp
    img = img * np.array([1 + temp, 1 + fix.get("tint", 0.0), 1 - temp], np.float32)
    if con != 1.0:
        img = (img - .42) * con + .42
    img = np.clip(img, 0, None)
    luma = img @ np.array([.2126, .7152, .0722], np.float32)
    # --- film look ---
    # gentle S-curve: deep but un-crushed shadows, soft highlight shoulder
    y = np.clip(luma, 0, 1.2)
    toe = y * y * (3 - 2 * np.clip(y, 0, 1)) * .25 + y * .75          # mild contrast
    shoulder = np.where(toe > .72, .72 + (1 - np.exp(-(toe - .72) / .26)) * .26, toe)
    tone = .012 + shoulder * .985
    ratio = (tone / np.maximum(luma, 1e-4))[..., None]
    img = img * ratio
    # saturation: restrained overall, rolled off further in the highlights (clean snow)
    s = sat * .94 * (1 - .35 * smoothstep(.75, 1.0, tone))[..., None]
    img = tone[..., None] + (img - tone[..., None]) * s
    # split tone: a breath of cool in the shadows, warmth in the highlights
    sh = (1 - smoothstep(0, .45, tone))[..., None]; hi = smoothstep(.55, 1, tone)[..., None]
    img = img + sh * np.array([-.012, .000, .016], np.float32) \
              + hi * np.array([.012, .004, -.012], np.float32)
    return np.clip(img, 0, 1)


_VIG = None
def finish(img, rng):
    """Light sharpen for the upscale, vignette, fine grain."""
    global _VIG
    pil = Image.fromarray((img * 255 + .5).astype(np.uint8))
    pil = pil.filter(ImageFilter.UnsharpMask(radius=2.2 * W / 1080, percent=55, threshold=2))
    img = np.asarray(pil, np.float32) / 255.0
    if _VIG is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((xx - W / 2) / (W * .75)) ** 2 + ((yy - H / 2) / (H * .62)) ** 2)
        _VIG = (1 - .22 * smoothstep(.55, 1.25, r))[..., None]
    img = img * _VIG
    g = rng.standard_normal((H, W), dtype=np.float32) * .016
    luma = img.mean(axis=2)
    img = img + (g * (1 - .6 * luma))[..., None]        # grain sits in the mids/shadows
    return np.clip(img, 0, 1)


# ---------------------------------------------------------------- title
TITLE_FACES = [("/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf", 104, 18),
               ("assets/CormorantGaramond-Italic.ttf", 132, 26),
               ("/usr/share/fonts/opentype/inter/Inter-Thin.otf", 104, 34),
               ("assets/CormorantGaramond-Italic.ttf", 132, 26),
               ("assets/CormorantGaramond.ttf", 128, 30)]      # last = the face it settles on


def title_layer(face=-1, sub=True):
    """ICELAND (+ subtitle) as (alpha, soft shadow). `face` picks the typeface."""
    S = W / 1080
    lay = Image.new("L", (W, H), 0); d = ImageDraw.Draw(lay)
    path, size, track = TITLE_FACES[face]
    f1 = ImageFont.truetype(path if path.startswith("/") else os.path.join(HERE, path), int(size * S))
    try:
        f1.set_variation_by_axes([500])
    except Exception:
        pass
    f2 = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Medium.otf", int(24 * S))

    def spaced(text, font, y, track):
        ws = [d.textlength(c, font=font) for c in text]
        x = (W - sum(ws) - track * (len(text) - 1)) / 2
        for c, w in zip(text, ws):
            d.text((x, y), c, font=font, fill=255, anchor="ls"); x += w + track
    y0 = int(H * .285)
    spaced("ICELAND", f1, y0, track * S)
    if sub:
        d.line([(W / 2 - 34 * S, y0 + 46 * S), (W / 2 + 34 * S, y0 + 46 * S)], fill=200, width=max(1, int(2 * S)))
        spaced("A WINTER ROAD TRIP", f2, y0 + 96 * S, 9 * S)
    a = np.asarray(lay, np.float32) / 255.0
    shadow = np.asarray(lay.filter(ImageFilter.GaussianBlur(14 * S)), np.float32) / 255.0
    return a, shadow


def apply_title(img, a, shadow, k):
    if k <= 0:
        return img
    img = img * (1 - .28 * k * shadow[..., None])
    return img + (np.array([.97, .96, .94], np.float32) - img) * (a * k)[..., None]


# ---------------------------------------------------------------- render
def track_sun(frames):
    """Centroid of the blown-out sun per frame -> smoothed cx (stabilises a yaw pan)."""
    xs = []
    for f in frames:
        l = f[::4, ::4].astype(np.float32).sum(axis=2)
        m = l > 250 * 3
        m[: int(m.shape[0] * .45)] = False; m[int(m.shape[0] * .8):] = False
        cols = m.sum(axis=0).astype(np.float32)
        xs.append((cols * np.arange(cols.size)).sum() / max(cols.sum(), 1) / cols.size)
    xs = np.array(xs); t = np.arange(len(xs))
    return np.polyval(np.polyfit(t, xs, 2), t)


def render_shot(shot):
    n_out = nframes(shot)
    start = sum(nframes(s) for s in SHOTS[: SHOTS.index(shot)])
    ts = [k[1] for k in shot["time"]]
    still = shot.get("still")
    if still:                                                 # photo: one frame, crop keyed 0..1
        frames = np.asarray(Image.open(src_path(shot["src"])).convert("RGB"))[None]
        fps, t_first = 1.0, 0.0
    else:
        frames, fps, t_first = decode(src_path(shot["src"]), min(ts), max(ts) + .2, shot.get("vf"),
                                      shot.get("interp", 1))
    sun = track_sun(frames) if shot.get("track_sun") else None
    fix = dict(shot.get("fix", {}))
    if shot.get("neutral"):
        fix["neutral"] = neutral_fit(frames[0])
    rng = np.random.default_rng(1000 + shot["id"])
    ttl = None
    if start < TITLE_OUT and start + n_out > TITLE_IN:
        ttl = [title_layer(i, sub=False) for i in range(len(TITLE_FACES) - 1)] + [title_layer(-1)]
    out = os.path.join(BUILD, f"shot{shot['id']:02d}.mkv")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "ffv1", "-level", "3", out],
        stdin=subprocess.PIPE)
    T = [smooth_time(shot["time"], i / n_out) for i in range(n_out + 1)]

    def sample(idx_f, zmul=1.0):
        i = int(np.clip(round(idx_f), 0, len(frames) - 1))
        tsrc = idx_f if still else t_first + i / fps
        cx, cy, zoom = interp_keys(shot["crop"], tsrc)
        if sun is not None:
            cx = float(sun[i])
        return crop_resize(frames[i], cx, cy, zoom * zmul)

    for n in range(n_out):
        a = (T[n] - t_first) * fps; b = (T[n + 1] - t_first) * fps
        zmuls = [1.0]
        if shot.get("zoom_out") and n >= n_out - 7:           # punch through the map
            k = (n - (n_out - 7)) / 6
            zmuls = [1 + 1.6 * k ** 2 * (1 + j * .12) for j in range(4)]
        if shot.get("zoom_in") and n < 8:                     # ...and land on the ice
            k = 1 - n / 8
            zmuls = [1 + .5 * k ** 2 * (1 + j * .15) for j in range(4)]
        acc = None; wsum = 0.0
        spd = (T[n + 1] - T[n]) * FPS
        if spd < .9:                                        # slowed (tracked shot): blend neighbours
            i0 = np.floor(a); fr = a - i0
            parts = [(i0, 1 - fr), (i0 + 1, fr)] if fr > .02 else [(i0, 1.0)]
        elif still:
            parts = [(n / max(n_out - 1, 1), 1.0)]
        elif spd < 2.5:                                     # near real-time: one crisp frame
            parts = [(a, 1.0)]
        else:                                                 # sped up: integrate = natural motion blur
            parts = []
            for i in range(int(np.floor(a)), int(np.ceil(b))):
                wgt = min(i + 1, b) - max(i, a)
                if wgt > .02:
                    parts.append((i, wgt))
        for zm in zmuls:
            for i, wgt in parts:
                im = sample(i, zm)
                acc = im * wgt if acc is None else acc + im * wgt
                wsum += wgt
        img = grade(acc / wsum, fix)
        img = finish(img, rng)
        g = start + n
        if ttl is not None and TITLE_IN <= g < TITLE_OUT:     # holds across the picture cut
            j = min((g - TITLE_IN) // 4, len(ttl) - 1)        # new typeface every 4 frames
            img = apply_title(img, ttl[j][0], ttl[j][1], 1.0)
        if shot.get("close_bars") and n >= n_out - shot["close_bars"]:
            k = (n - (n_out - shot["close_bars"]) + 1) / (shot["close_bars"] - 2)
            bar = int(min(1.0, k) ** 1.6 * H / 2)
            if bar:
                img[:bar] = 0; img[H - bar:] = 0
        if shot.get("flash") and n < 5:
            img = np.clip(img + .16 * (1 - n / 5) ** 2, 0, 1)
        if shot.get("to_white") and n >= n_out - shot["to_white"]:
            k = (n - (n_out - shot["to_white"]) + 1) / shot["to_white"]
            img = img + (1 - img) * k ** 1.5
        if shot.get("from_white") and n < shot["from_white"]:
            k = 1 - n / shot["from_white"]
            img = img + (np.array([1, .97, .92], np.float32) - img) * k ** 1.6
        if shot.get("from_black") and n < shot["from_black"]:
            img = img * smoothstep(0, 1, (n + 1) / shot["from_black"])
        if shot.get("fade_out") and n >= n_out - shot["fade_out"]:
            k = (n_out - 1 - n) / shot["fade_out"]
            img = img * smoothstep(0, 1, k)
        enc.stdin.write((img * 255 + .5).astype(np.uint8).tobytes())
    enc.stdin.close(); enc.wait()
    return shot["id"]


def main():
    os.makedirs(BUILD, exist_ok=True); os.makedirs(OUT, exist_ok=True)
    only = None
    if "--only" in sys.argv:
        only = {int(x) for x in sys.argv[sys.argv.index("--only") + 1].split(",")}
    todo = [s for s in SHOTS if only is None or s["id"] in only]
    with Pool(4) as p:
        for sid in p.imap_unordered(render_shot, todo):
            print("rendered shot", sid, flush=True)
    lst = os.path.join(BUILD, "concat.txt")
    with open(lst, "w") as f:
        for s in SHOTS:
            f.write(f"file 'shot{s['id']:02d}.mkv'\n")
    score = os.path.join(BUILD, "score.wav")
    if not os.path.exists(score):
        subprocess.check_call([sys.executable, os.path.join(HERE, "score.py")])
    final = os.path.join(OUT, "iceland_preview.mp4" if PREVIEW else "iceland_winter_road_trip_9x16.mp4")
    subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
        "-i", score, "-c:v", "libx264", "-preset", "fast" if PREVIEW else "slow",
        "-crf", "22" if PREVIEW else "18", "-maxrate", "14M", "-bufsize", "28M",
        "-profile:v", "high", "-pix_fmt", "yuv420p",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-r", str(FPS), "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
        "-t", f"{TOTAL / FPS:.3f}", "-movflags", "+faststart", final])
    print("wrote", final)


if __name__ == "__main__":
    main()
