import base64
import os
import urllib.request
import numpy as np
import cv2
from PIL import Image

# 1. Download JetBrains Mono font subset if not local
FONT_URL = "https://raw.githubusercontent.com/andriidrok1/andriidrok1/main/fonts/ramp.woff2"
font_path = "ramp.woff2"

if not os.path.exists(font_path):
    try:
        urllib.request.urlretrieve(FONT_URL, font_path)
    except Exception as e:
        print(f"Warning: Could not download font: {e}")

# Settings
COLS = 95
DISPLAY_WIDTH = 460
# ' ' space is first so transparent background areas remain completely empty
RAMP = ' .`:-=+*cs#%@'

# 2. Load PNG Image with Alpha Channel
image_file = None
for name in ["photo.png", "photo.PNG", "photo.jpg"]:
    if os.path.exists(name):
        image_file = name
        break

if not image_file:
    raise FileNotFoundError("Could not find photo.png in repository root")

print(f"Loading image: {image_file}")
img = Image.open(image_file).convert("RGBA")

# Extract RGB and Alpha channels
arr = np.array(img)
rgb, alpha = arr[:, :, :3], arr[:, :, 3]

# Convert RGB to Grayscale
gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

# FORCE all transparent/background pixels (alpha < 128) to pure white (255)
# In RAMP, 255 maps directly to ' ' (blank space)
gray[alpha < 128] = 255

# Apply CLAHE local contrast enhancement ONLY to visible subject
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
gray = clahe.apply(gray)

# Slight contrast adjustment for clear facial features
gray = np.power(gray / 255.0, 1.1) * 255.0

# Re-apply transparent background mask after contrast adjustment
gray[alpha < 128] = 255

# Downscale image to match character aspect ratio
rows = int(COLS * (gray.shape[0] / gray.shape[1]) * 0.48)
resized = cv2.resize(gray, (COLS, rows), interpolation=cv2.INTER_AREA)

# Map pixels to character ramp
ramp_len = len(RAMP)
lines = []
for row in resized:
    line = "".join(RAMP[min(int(val / 256 * ramp_len), ramp_len - 1)] for val in row)
    lines.append(line)

# Load font base64
font_b64 = ""
if os.path.exists(font_path):
    with open(font_path, "rb") as f:
        font_b64 = base64.b64encode(f.read()).decode("utf-8")

# 3. Build Animated SVG
char_w, char_h = 7.74, 15.48
view_w, view_h = COLS * char_w, rows * char_h

svg = [
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {view_w:.2f} {view_h:.2f}" width="{DISPLAY_WIDTH}">',
    '  <style>'
]

if font_b64:
    svg.append(f'    @font-face {{ font-family: "CustomMono"; src: url("data:font/woff2;base64,{font_b64}") format("woff2"); }}')

svg.extend([
    '    text { font-family: "CustomMono", monospace; font-size: 12.9px; fill: #e6edf3; xml:space: preserve; }',
    '  </style>',
    '  <defs>'
])

for i in range(rows):
    delay = i * 0.09
    svg.append(f'    <clipPath id="cp-{i}">')
    svg.append(f'      <rect x="0" y="{i * char_h:.2f}" height="{char_h:.2f}" width="0">')
    svg.append(f'        <animate attributeName="width" from="0" to="{view_w:.2f}" dur="0.2s" begin="{delay:.2f}s" fill="freeze" />')
    svg.append(f'      </rect>')
    svg.append(f'    </clipPath>')

svg.append('  </defs>')

for i, line in enumerate(lines):
    svg.append(f'  <text y="{(i + 1) * char_h - 3:.2f}" clip-path="url(#cp-{i})">{line}</text>')

svg.append('</svg>')

with open("portrait.svg", "w", encoding="utf-8") as f:
    f.write("\n".join(svg))

print("Successfully generated portrait.svg")
