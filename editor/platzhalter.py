"""Creates a placeholder 'presenter' video (only for demos, until a real recording exists).
Usage: python3 editor/platzhalter.py <ausgabe.mp4> <sekunden>"""
import subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont
out, dur = sys.argv[1], sys.argv[2]
W, H = 1080, 1920
img = Image.new("RGB", (W, H))
d = ImageDraw.Draw(img)
for y in range(H):  # warm room gradient
    k = y / H
    d.line([(0, y), (W, y)], fill=(int(70 - 30 * k), int(58 - 25 * k), int(62 - 20 * k)))
bok = Image.new("RGBA", (W, H), (0, 0, 0, 0)); b = ImageDraw.Draw(bok)
for x, y, r, c in [(160, 300, 90, (255, 200, 120, 90)), (900, 420, 120, (120, 200, 255, 70)), (820, 1100, 70, (255, 170, 90, 80)),
                   (200, 1000, 110, (180, 140, 255, 60)), (540, 200, 60, (255, 230, 160, 70))]:
    b.ellipse([x - r, y - r, x + r, y + r], fill=c)
img = Image.alpha_composite(img.convert("RGBA"), bok.filter(ImageFilter.GaussianBlur(40)))
sil = Image.new("RGBA", (W, H), (0, 0, 0, 0)); s = ImageDraw.Draw(sil)
s.ellipse([400, 430, 680, 760], fill=(28, 26, 32, 255))            # head
s.rounded_rectangle([230, 820, 850, 1920], radius=260, fill=(28, 26, 32, 255))  # shoulders
s.rectangle([480, 740, 600, 860], fill=(28, 26, 32, 255))          # neck
img = Image.alpha_composite(img, sil.filter(ImageFilter.GaussianBlur(3)))
d = ImageDraw.Draw(img)
f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 34)
d.text((W / 2, 1800), "PLATZHALTER: hier bist du (deine Aufnahme)", font=f, fill=(255, 255, 255, 140), anchor="mm")
img.convert("RGB").save("/tmp/_ph.png")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", "/tmp/_ph.png", "-t", dur, "-r", "30",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", out], check=True)
print("placeholder written", out)
