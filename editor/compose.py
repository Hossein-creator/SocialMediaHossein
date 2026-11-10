"""Compositor v2: assembles the final video frame by frame.
Usage (in the venv with numpy, opencv, mediapipe):
  python editor/compose.py <projekt> <aufnahme.mp4|.png> <under-frames> <over-frames> <audio.wav> <ausgabe.mp4>

Layers (bottom to top):
  1. background (workspace image, blurred = depth of field, slow camera movement)
  2. B-roll/slides ("under" layer)
  3. you: cut out (segmentation), rim light + shadow, layout per scene:
       full = full frame + punch-in zooms | split = B-roll top, you bottom
       pip = B-roll full screen, you in a circle | broll = only B-roll (voice-over)
  4. subtitles, titles, stickers ("over" layer)
  5. global effects: whip transition, glitch, shake, flash, light leak, colour grade, vignette, grain
Audio: voice cleaned (high-pass, denoise, compressor, loudness) + music/SFX, which duck while you speak."""
import json, os, subprocess, sys
import cv2
import numpy as np

proj, rec, under_dir, over_dir, bed, out = sys.argv[1:7]
tl = json.load(open(f"{proj}/timeline.json", encoding="utf-8"))
FPS, D = tl.get("fps", 30), tl["duration"]
W, H = 1080, 1920
N = int(round(D * FPS))
rng = np.random.default_rng(1)
here = os.path.dirname(os.path.abspath(__file__))

# ---------------- helpers ----------------
def ease(x):
    x = min(max(x, 0.0), 1.0)
    return 4 * x * x * x if x < .5 else 1 - (-2 * x + 2) ** 3 / 2

def load_rgba(path):
    if not path or not os.path.exists(path):
        return None
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if im is None:
        return None
    if im.ndim == 2:
        im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
    if im.shape[2] == 3:  # fully opaque frames are saved without an alpha channel
        im = np.dstack([im, np.full(im.shape[:2], 255, np.uint8)])
    return im

def over(dst, rgba):
    """alpha-composite an RGBA uint8 image (BGR order) over float32 BGR dst (0..1)"""
    if rgba is None:
        return dst
    a = rgba[:, :, 3:4].astype(np.float32) / 255.0
    if a.max() == 0:
        return dst
    return dst * (1 - a) + rgba[:, :, :3].astype(np.float32) / 255.0 * a

def cover(img, w, h):
    ih, iw = img.shape[:2]
    s = max(w / iw, h / ih)
    img = cv2.resize(img, (int(iw * s + .5), int(ih * s + .5)), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    y, x = (img.shape[0] - h) // 2, (img.shape[1] - w) // 2
    return img[y:y + h, x:x + w]

# ---------------- background ----------------
bg_path = tl.get("background") or os.path.join(here, "..", "design", "hintergruende", "studio.png")
bg_src = cv2.imread(bg_path)
if bg_src is None:
    bg_src = np.full((H, W, 3), (40, 24, 12), np.uint8)
BGS = 1.12
bg_big = cover(bg_src, int(W * BGS), int(H * BGS))
bg_big = cv2.GaussianBlur(bg_big, (0, 0), tl.get("backgroundBlur", 5)).astype(np.float32) / 255.0
bg_big = np.clip((bg_big - .5) * 1.05 + .5 - .03, 0, 1)  # a little contrast, slightly darker so you stand out

def background(t):
    mx, my = bg_big.shape[1] - W, bg_big.shape[0] - H
    x = int(mx / 2 + mx / 2 * .8 * np.sin(t * .12))
    y = int(my / 2 + my / 2 * .6 * np.sin(t * .09 + 1))
    return bg_big[y:y + H, x:x + W].copy()

# ---------------- presenter source ----------------
still = None
if rec.lower().endswith(".png"):
    still = load_rgba(rec)
    still = cover(still, W, H)
    cap = None
else:
    cap = cv2.VideoCapture(rec)
    src_fps = cap.get(cv2.CAP_PROP_FPS) or FPS
seg = None
if still is None and not tl.get("keepOriginalBackground"):
    import mediapipe as mp
    seg = mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=0)

last_frame, last_mask, src_idx = None, None, -1
def presenter(t):
    """returns (bgr float32, mask float32 0..1)"""
    global last_frame, last_mask, src_idx
    if still is not None:
        return still[:, :, :3].astype(np.float32) / 255, still[:, :, 3].astype(np.float32) / 255
    want = int(t * src_fps)
    while src_idx < want:
        ok, fr = cap.read()
        if not ok:
            break
        src_idx += 1
        last_frame = cover(fr, W, H)
        if seg is not None:
            small = cv2.resize(last_frame, (360, 640))
            m = seg.process(cv2.cvtColor(small, cv2.COLOR_BGR2RGB)).segmentation_mask
            m = cv2.resize(m, (W, H), interpolation=cv2.INTER_LINEAR)
            m = np.clip((m - .35) / .3, 0, 1)                      # sharper edge
            m = cv2.GaussianBlur(m, (0, 0), 2.2)
            last_mask = m if last_mask is None else .55 * m + .45 * last_mask   # temporal smoothing (less flicker)
        else:
            last_mask = np.ones((H, W), np.float32)
    return last_frame.astype(np.float32) / 255, last_mask

# face anchor: from the mask of the first frame (top of the person + 13% of the height)
def face_anchor():
    _, m = presenter(0.0)
    ys = np.where(m.max(axis=1) > .5)[0]
    if len(ys) == 0:
        return (W / 2, H * .33)
    top = ys[0]
    row = m[min(top + 120, H - 1)]
    xs = np.where(row > .5)[0]
    cx = xs.mean() if len(xs) else W / 2
    return (float(cx), float(top + .07 * H))
FACE = tuple(tl.get("faceAnchor") or face_anchor())

# ---------------- layouts ----------------
scenes = tl.get("scenes", [{"t0": 0, "t1": D, "layout": "full"}])
zooms = tl.get("zooms", [])

def zoom_at(t):
    z = 1.0
    for s in zooms:
        if s["t0"] <= t < s["t1"]:
            k = ease((t - s["t0"]) / .18)  # quick punch-in
            z = 1 + (s["z"] - 1) * k
    return z

def layout_params(name, t):
    if name == "full":
        z = zoom_at(t)
        return dict(s=z, x=FACE[0], y=FACE[1], circle=0.0, vis=1.0)
    if name == "split":
        return dict(s=.74, x=W / 2, y=1290, circle=0.0, vis=1.0)
    if name == "pip":
        return dict(s=.46, x=250, y=1590, circle=1.0, vis=1.0)
    return dict(s=.46, x=250, y=1590, circle=1.0, vis=0.0)  # broll

def params(t):
    i = next((k for k, s in enumerate(scenes) if s["t0"] <= t < s["t1"]), len(scenes) - 1)
    cur = layout_params(scenes[i].get("layout", "full"), t)
    if i > 0:
        k = ease((t - scenes[i]["t0"]) / .4)
        if k < 1:
            prev = layout_params(scenes[i - 1].get("layout", "full"), t)
            cur = {key: prev[key] + (cur[key] - prev[key]) * k for key in cur}
    return cur

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

def place_presenter(frame, rgb, m, p, t):
    if p["vis"] <= 0.01:
        return frame
    s = p["s"]
    M = np.float32([[s, 0, p["x"] - s * FACE[0]], [0, s, p["y"] - s * FACE[1]]])
    rgb_w = cv2.warpAffine(rgb, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    m_w = cv2.warpAffine(m, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    cyan = np.array([.93, .83, .13], np.float32)  # BGR
    # (a) cut-out version: shadow + rim light, you over the background
    sh = np.roll(cv2.GaussianBlur(m_w, (0, 0), 25), 25, axis=1)[..., None]
    cut = frame * (1 - .45 * sh)
    edge = np.clip(m_w - cv2.erode(m_w, np.ones((9, 9), np.uint8)), 0, 1)
    edge = cv2.GaussianBlur(edge, (0, 0), 6)[..., None]
    rim = np.where((xx < p["x"])[..., None], cyan, np.array([.98, .55, .65], np.float32))
    pres = np.clip(rgb_w + edge * rim * .55, 0, 1)
    a = m_w[..., None]
    cut = cut * (1 - a) + pres * a
    if p["circle"] <= 0.01:
        res = cut
    else:
        # (b) bubble version: you in a round frame with a glowing ring (B-roll stays visible)
        R = 200.0
        cy = p["y"] + 60
        d = np.sqrt((xx - p["x"]) ** 2 + (yy - cy) ** 2)
        disc = np.clip((R - d) / 2.5, 0, 1)[..., None]
        bub = frame * (1 - disc) + (frame * .25 * (1 - a) + pres * a) * disc
        ring = np.clip(1 - np.abs(d - R) / 6, 0, 1)
        glow = cv2.GaussianBlur(ring, (0, 0), 14)[..., None]
        bub = np.clip(bub * (1 - ring[..., None]) + cyan * ring[..., None] + glow * cyan * .6, 0, 1)
        res = cut * (1 - p["circle"]) + bub * p["circle"]
    return frame * (1 - p["vis"]) + res * p["vis"]

# ---------------- global effects ----------------
fx = tl.get("fx", [])
vign = 1 - .45 * np.clip(((xx - W / 2) / (W * .75)) ** 2 + ((yy - H / 2) / (H * .7)) ** 2, 0, 1)
vign = vign[..., None].astype(np.float32)

def fx_active(kind, t):
    for e in fx:
        if e["type"] == kind and e["t"] <= t < e["t"] + e.get("dur", .3):
            return e, (t - e["t"]) / e.get("dur", .3)
    return None, 0

def apply_fx(fr, t):
    e, k = fx_active("whip", t)
    if e:
        strength = np.sin(k * np.pi)
        L = int(5 + 80 * strength)
        ker = np.zeros((1, L), np.float32); ker[0, :] = 1 / L
        fr = cv2.filter2D(fr, -1, ker)
        shift = int((k - .5) * 220 * (1 if e.get("dir", 1) > 0 else -1))
        fr = np.roll(fr, shift, axis=1)
    e, k = fx_active("shake", t)
    if e:
        a = (1 - k) * e.get("amp", 22)
        fr = np.roll(fr, (int(rng.uniform(-a, a)), int(rng.uniform(-a, a))), axis=(0, 1))
    e, k = fx_active("glitch", t)
    if e:
        o = int(14 * (1 - k) + 4)
        b, g, r = fr[..., 0], fr[..., 1], fr[..., 2]
        fr = np.stack([np.roll(b, -o, 1), g, np.roll(r, o, 1)], -1)
        for _ in range(6):
            y0 = int(rng.uniform(0, H - 80)); h = int(rng.uniform(10, 80))
            fr[y0:y0 + h] = np.roll(fr[y0:y0 + h], int(rng.uniform(-60, 60)), axis=1)
    e, k = fx_active("flash", t)
    if e:
        fr = fr + (1 - fr) * (.7 * (1 - k))
    e, k = fx_active("leak", t)
    if e:
        a = np.sin(k * np.pi) * .55
        cx = W * (1.2 - 1.4 * k)
        leak = np.exp(-(((xx - cx) / 420) ** 2 + ((yy - H * .3) / 900) ** 2))[..., None]
        fr = 1 - (1 - fr) * (1 - leak * a * np.array([.25, .55, 1.0], np.float32))  # screen blend, warm orange
    # grade: teal shadows / warm highlights, saturation, vignette, grain
    lum = fr.mean(axis=2, keepdims=True)
    fr = fr + (lum - .5) * np.array([.05, .0, -.05], np.float32) * -1
    fr = lum + (fr - lum) * 1.12
    fr = fr * vign
    fr = fr + rng.normal(0, .012, (H // 4, W // 4, 1)).astype(np.float32).repeat(4, 0).repeat(4, 1)
    return np.clip(fr, 0, 1)

# ---------------- main loop ----------------
has_audio = (not rec.lower().endswith(".png")) and subprocess.run(
    ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", rec],
    capture_output=True, text=True).stdout.strip() != ""
cmd = ["ffmpeg", "-y", "-loglevel", "error",
       "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
if has_audio:
    cmd += ["-i", rec]
cmd += ["-i", bed]
bi = 2 if has_audio else 1
if has_audio:
    af = ("[1:a]highpass=f=80,afftdn=nf=-25,acompressor=threshold=-20dB:ratio=3:attack=5:release=120,"
          "loudnorm=I=-15:TP=-1.5:LRA=7,asplit=2[voice][sc];"
          f"[{bi}:a][sc]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[duck];"
          "[voice][duck]amix=inputs=2:duration=first:normalize=0[a]")
else:
    af = f"[{bi}:a]anull[a]"
cmd += ["-filter_complex", af, "-map", "0:v", "-map", "[a]", "-t", str(D),
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
preview = os.environ.get("PREVIEW")  # e.g. PREVIEW="1,12.5,30" -> writes single PNG frames instead of a video
if preview:
    frames_idx = [int(round(float(x) * FPS)) for x in preview.split(",")]
    os.makedirs(out, exist_ok=True)
else:
    frames_idx = range(N)
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)

for i in frames_idx:
    t = i / FPS
    frame = background(t)
    p = params(t)
    if p["vis"] < .99 or p["s"] < .99 or p["circle"] > 0:  # under layer only matters when B-roll is visible
        frame = over(frame, load_rgba(f"{under_dir}/f{i:05d}.png"))
    rgb, m = presenter(t)
    frame = place_presenter(frame, rgb, m, p, t)
    frame = over(frame, load_rgba(f"{over_dir}/f{i:05d}.png"))
    frame = apply_fx(frame, t)
    if preview:
        cv2.imwrite(f"{out}/p{i:05d}.png", (frame * 255).astype(np.uint8)); continue
    ff.stdin.write((frame * 255).astype(np.uint8).tobytes())
    if i % 300 == 0:
        print(f"compose {i}/{N}", flush=True)
if not preview:
    ff.stdin.close(); ff.wait()
print("written", out)
