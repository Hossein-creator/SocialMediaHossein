"""Combines your recording + graphics layer + music/SFX into the final video.
Usage: python3 editor/compose.py <projekt-ordner> <aufnahme.mp4> <frames-ordner> <audio.wav> <ausgabe.mp4>

- Video: fill 9:16, punch-in zooms from timeline.json, short shake on the hook, colour grade, vignette
- Audio: voice (cleaned up: high-pass, compressor, loudness) + music, which ducks automatically while you speak"""
import json, subprocess, sys

proj, rec, frames, bed, out = sys.argv[1:6]
tl = json.load(open(f"{proj}/timeline.json", encoding="utf-8"))
fps, D = tl.get("fps", 30), tl["duration"]

# zoom factor as a piecewise expression over input time
z = "1"
for s in tl.get("zooms", []):
    z += f"+{s['z'] - 1:.3f}*between(it,{s['t0']},{s['t1']})"
shake = "if(lt(it,0.4),10*sin(it*70),0)"

has_audio = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                            "-of", "csv=p=0", rec], capture_output=True, text=True).stdout.strip() != ""

vf = (f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps={fps},"
      f"scale=2160:3840,zoompan=z='{z}':x='iw/2-(iw/zoom/2)+{shake}':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps={fps},"
      f"eq=contrast=1.07:saturation=1.15:gamma=0.98,vignette=PI/5[base];"
      f"[base][1:v]overlay=0:0:format=auto,format=yuv420p[v]")

if has_audio:
    af = ("[0:a]highpass=f=80,afftdn=nf=-25,acompressor=threshold=-20dB:ratio=3:attack=5:release=120,"
          "loudnorm=I=-15:TP=-1.5:LRA=7,asplit=2[voice][sc];"
          "[2:a][sc]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[bedduck];"
          "[voice][bedduck]amix=inputs=2:duration=first:normalize=0[a]")
else:
    af = "[2:a]anull[a]"

cmd = ["ffmpeg", "-y", "-loglevel", "error", "-stats",
       "-i", rec,
       "-framerate", str(fps), "-i", f"{frames}/f%05d.png",
       "-i", bed,
       "-filter_complex", vf + ";" + af,
       "-map", "[v]", "-map", "[a]", "-t", str(D),
       "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
subprocess.run(cmd, check=True)
print("video written", out)
