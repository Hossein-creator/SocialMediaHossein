"""Demo only: transparent placeholder 'presenter' (a silhouette) as PNG, used instead of a real recording.
Usage: python3 editor/platzhalter.py <ausgabe.png>"""
import sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont
W, H = 1080, 1920
img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
s = ImageDraw.Draw(img)
col = (52, 48, 60, 255)
s.ellipse([400, 430, 680, 760], fill=col)
s.rectangle([480, 740, 600, 860], fill=col)
s.rounded_rectangle([230, 820, 850, 2100], radius=260, fill=col)
img = img.filter(ImageFilter.GaussianBlur(2))
d = ImageDraw.Draw(img)
f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
d.text((W / 2, 1150), "PLATZHALTER", font=f, fill=(255, 255, 255, 150), anchor="mm")
d.text((W / 2, 1195), "hier bist du", font=f, fill=(255, 255, 255, 150), anchor="mm")
img.save(sys.argv[1]); print("saved", sys.argv[1])
