"""Demo helper only: generates estimated word timings from script sentences
(for a real recording, transcribe.py provides exact timings).
Usage: python3 editor/words_from_script.py <projekt-ordner>   (reads script.json, writes words.json)
script.json: [{"t0": 0.2, "t1": 3.0, "text": "..."}]"""
import json, sys
proj = sys.argv[1]
words = []
for s in json.load(open(f"{proj}/script.json", encoding="utf-8")):
    toks = s["text"].split()
    total = sum(len(t) + 2 for t in toks)
    t = s["t0"]
    for tok in toks:
        d = (s["t1"] - s["t0"]) * (len(tok) + 2) / total
        words.append({"w": tok, "t0": round(t, 3), "t1": round(t + d * 0.92, 3)})
        t += d
json.dump(words, open(f"{proj}/words.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print(len(words), "words")
