"""Generates background music and sound effects for a project (no downloads, everything synthesized).
Usage: python3 editor/audio.py <projekt-ordner> <ausgabe.wav>
Writes a stereo 48 kHz track containing the music bed plus all sound effects from timeline.json."""
import json, sys, wave
import numpy as np

SR = 48000
rng = np.random.default_rng(7)

def env(n, a, r):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    if na: e[:na] = np.linspace(0, 1, na)
    if nr: e[-nr:] *= np.linspace(1, 0, nr)
    return e

def lowpass(x, cutoff):
    """One-pole low-pass; cutoff may be an array (sweep)."""
    cutoff = np.broadcast_to(cutoff, x.shape)
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x); s = 0.0
    for i in range(len(x)):
        s = (1 - a[i]) * x[i] + a[i] * s
        y[i] = s
    return y

def note(f):  # midi -> Hz
    return 440 * 2 ** ((f - 69) / 12)

# ---------- sound effects ----------
def sfx_whoosh(d=0.45):
    n = int(d * SR); t = np.linspace(0, 1, n)
    x = rng.standard_normal(n)
    x = lowpass(x, 300 + 5000 * np.sin(np.pi * t) ** 2)
    return 0.9 * x / np.abs(x).max() * np.sin(np.pi * t) ** 1.5

def sfx_swish():
    return 0.7 * sfx_whoosh(0.25)

def sfx_pop():
    n = int(0.12 * SR); t = np.arange(n) / SR
    f = 900 * np.exp(-t * 25) + 250
    return 0.8 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 35)

def sfx_click():
    n = int(0.03 * SR)
    return 0.6 * rng.standard_normal(n) * np.exp(-np.arange(n) / SR * 200)

def sfx_ding():
    n = int(0.9 * SR); t = np.arange(n) / SR
    return 0.35 * (np.sin(2 * np.pi * 1318 * t) + 0.5 * np.sin(2 * np.pi * 2637 * t)) * np.exp(-t * 5)

def sfx_boom():
    n = int(0.7 * SR); t = np.arange(n) / SR
    f = 110 * np.exp(-t * 6) + 40
    return 0.9 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5)

def sfx_typing(d=1.0):
    n = int(d * SR); y = np.zeros(n)
    t = 0.0
    while t < d - 0.05:
        k = sfx_click() * rng.uniform(0.4, 0.8)
        i = int(t * SR); y[i:i + len(k)] += k[: n - i]
        t += rng.uniform(0.06, 0.11)
    return y

SFX = {"whoosh": sfx_whoosh, "swish": sfx_swish, "pop": sfx_pop, "click": sfx_click,
       "ding": sfx_ding, "boom": sfx_boom, "typing": sfx_typing}

# ---------- music: calm lo-fi loop (Am - F - C - G) ----------
def music(duration, bpm):
    n = int(duration * SR); y = np.zeros((n, 2))
    beat = 60 / bpm; bar = 4 * beat
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
    bass = [45, 41, 36, 43]
    t_bar = 0.0; k = 0
    while t_bar < duration:
        i0 = int(t_bar * SR); L = min(int(bar * SR), n - i0)
        if L <= 0: break
        t = np.arange(L) / SR
        pad = sum(np.sin(2 * np.pi * note(m) * t) + 0.3 * np.sin(2 * np.pi * 2 * note(m) * t + .3) for m in chords[k % 4])
        pad *= 0.06 * env(L, 0.25, 0.3)
        b = 0.12 * np.sin(2 * np.pi * note(bass[k % 4]) * t) * env(L, 0.02, 0.2)
        y[i0:i0 + L, 0] += pad + b
        y[i0:i0 + L, 1] += np.roll(pad, 240) + b
        # drums
        for s in range(8):
            ts = t_bar + s * beat / 2
            j = int(ts * SR)
            if j >= n: break
            if s in (0, 4):
                kk = 0.35 * sfx_boom()[: int(.25 * SR)]
            elif s in (2, 6):
                kk = 0.12 * lowpass(rng.standard_normal(int(.15 * SR)), 2500) * np.exp(-np.arange(int(.15 * SR)) / SR * 25)
            else:
                kk = 0.04 * rng.standard_normal(int(.04 * SR)) * np.exp(-np.arange(int(.04 * SR)) / SR * 120)
            m = min(len(kk), n - j)
            y[j:j + m] += kk[:m, None]
        t_bar += bar; k += 1
    y *= env(n, 1.0, 2.0)[:, None]
    return y

def main():
    proj, out = sys.argv[1], sys.argv[2]
    tl = json.load(open(f"{proj}/timeline.json", encoding="utf-8"))
    D = tl["duration"]; n = int(D * SR)
    mcfg = tl.get("music", {})
    mix = np.zeros((n, 2))
    if mcfg.get("gainDb") is not None:
        m = music(D, mcfg.get("bpm", 96))
        mix += m / np.abs(m).max() * 10 ** (mcfg["gainDb"] / 20)
    for e in tl.get("sfx", []):
        f = SFX[e["name"]]
        s = f(e["dur"]) if "dur" in e else f()
        s = s * 10 ** (e.get("gainDb", -8) / 20)
        i = int(e["t"] * SR); m = min(len(s), n - i)
        if m > 0: mix[i:i + m] += s[:m, None]
    peak = np.abs(mix).max()
    if peak > 0.98: mix *= 0.98 / peak
    with wave.open(out, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype("<i2").tobytes())
    print("audio written", out)

if __name__ == "__main__":
    main()
