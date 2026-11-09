"""Generates virtual background images (workspace) with SD-Turbo (runs on the CPU).
Usage: python editor/hintergrund.py <ausgabe-ordner> [anzahl] ["eigener prompt"]
The model (stabilityai/sd-turbo) is downloaded from Hugging Face on first use."""
import os, sys
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
import torch
from diffusers import AutoPipelineForText2Image

out = sys.argv[1]
n = int(sys.argv[2]) if len(sys.argv) > 2 else 4
prompt = sys.argv[3] if len(sys.argv) > 3 else (
    "photo of a modern programmer workspace at night, wooden desk with two monitors showing colorful code, "
    "mechanical keyboard with RGB, cyan and purple LED strip lights on the wall, shelves with gadgets and "
    "arduino boards, small plants, neon sign, cozy, cinematic lighting, depth of field, bokeh, highly detailed, 8k")
os.makedirs(out, exist_ok=True)
torch.set_num_threads(os.cpu_count())
pipe = AutoPipelineForText2Image.from_pretrained("stabilityai/sd-turbo", torch_dtype=torch.float32)
for i in range(n):
    g = torch.Generator().manual_seed(100 + i)
    img = pipe(prompt=prompt, num_inference_steps=2, guidance_scale=0.0, width=512, height=896, generator=g).images[0]
    p = os.path.join(out, f"workspace_{i + 1}.png")
    img.save(p)
    print("saved", p, flush=True)
