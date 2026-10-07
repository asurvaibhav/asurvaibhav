import base64
import os
import urllib.request
import numpy as np
import cv2
from rembg import remove
from PIL import Image

# 1. Download Font
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
RAMP = ' .`:-=+*cs#%@'

# 2. Find Image
image_file = None
for name in ["photo.png", "photo.PNG", "photo.jpg", "photo.jpeg"]:
    if os.path.exists(name):
        image_file = name
        break

if not image_file:
    raise FileNotFoundError("Could not find photo file in root directory.")

print(f"Loading image: {image_file}")
raw_img = Image.open(image_file)

# Remove background cleanly
img_no_bg = remove(raw_img)

# Convert to numpy array
arr = np.array(img_no_bg)

# If image has 3 channels (RGB), add full alpha
if arr.shape[2] == 3:
    alpha = np.full((arr.shape[0], arr.shape[1]), 255, dtype=np.uint8)
    rgb = arr
else:
    rgb = arr[:, :, :3]
    alpha = arr[:, :, 3]

# Convert RGB to Grayscale
gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

# Downscale gray image AND alpha mask together to match target grid size
rows = int(COLS * (gray.shape[0] / gray.shape[1]) * 0.48)
gray_resized = cv2.resize(gray, (COLS, rows), interpolation=cv2.INTER_AREA)
alpha_resized = cv2.resize(alpha, (COLS, rows), interpolation=cv2.INTER_AREA)

# Contrast adjustment ONLY on non-transparent subject pixels
bg_mask = alpha_resized < 100
gray_resized[bg_mask] = 255  # Set background to max value (255)

# Equalize contrast for subject
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
subject_enhanced = clahe.apply(gray_resized)

# Re-apply strict background override AFTER CLAHE (CLAHE modifies all values)
subject_enhanced[bg_mask] = 255

# Map pixels to character ramp
ramp_len = len(RAMP)
lines = []
for row in subject_enhanced:
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

print("Successfully regenerated portrait.svg with transparent background")
