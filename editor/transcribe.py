"""Transcribes your recording (Persian) with word-level timestamps.
Usage: python editor/transcribe.py <aufnahme.mp4> <ausgabe-words.json> [modell]
Output: [{"w": "word", "t0": 1.23, "t1": 1.56}, ...]
The model (default: large-v3-turbo) is downloaded from Hugging Face on first use."""
import json, os, sys
from faster_whisper import WhisperModel

src, out = sys.argv[1], sys.argv[2]
name = sys.argv[3] if len(sys.argv) > 3 else "large-v3-turbo"
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
root = os.environ.get("WHISPER_DIR", os.path.expanduser("~/.cache/whisper-models"))

model = WhisperModel(name, device="cpu", compute_type="int8", download_root=root)
segments, info = model.transcribe(
    src, language="fa", word_timestamps=True, vad_filter=True, beam_size=5,
    # Tech terms in Latin script, so Whisper writes them as "IP" rather than "آی‌پی"
    initial_prompt="آموزش کامپیوتر به فارسی: IP، MAC، Router، Switch، Linux، Arduino، ESP32، DNS، DHCP، AI، ChatGPT.")
words = []
for seg in segments:
    for w in seg.words or []:
        t = w.word.strip()
        if t:
            words.append({"w": t, "t0": round(w.start, 3), "t1": round(w.end, 3)})
json.dump(words, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print(f"{len(words)} words, {info.duration:.1f}s ->", out)
