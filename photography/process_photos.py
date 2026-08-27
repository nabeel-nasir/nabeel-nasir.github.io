#!/usr/bin/env python3
"""
Resize and watermark photos for the photography page.

Usage:
    python3 process_photos.py

Drop full-resolution originals into photography/originals/, then run this
script. For each photo it:
  - reads the capture date and GPS location from EXIF (before it's stripped)
  - reverse-geocodes the GPS coordinates into a "City, State/Country" string
  - resizes the image, adds a watermark, and strips all EXIF metadata
  - writes the result to images/photography/
  - records month/year/location in images/photography/manifest.js

Add the output filenames to the `photos` array in photography.html to show
them in the gallery; captions are pulled from manifest.js automatically.
"""

import json
import os
import time
import urllib.parse
import urllib.request

import pillow_heif
from PIL import Image, ImageDraw, ImageFont, ImageOps

pillow_heif.register_heif_opener()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(SCRIPT_DIR, "originals")
DST_DIR = os.path.join(SCRIPT_DIR, "..", "images", "photography")
MANIFEST_PATH = os.path.join(DST_DIR, "manifest.js")

MAX_DIMENSION = 1600
JPEG_QUALITY = 82
WATERMARK_TEXT = "© Nabeel Nasir"
FONT_PATH = "/System/Library/Fonts/Supplemental/Arial.ttf"

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

_geocode_cache = {}


def add_watermark(img):
    img = img.convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    font_size = max(16, img.width // 40)
    font = ImageFont.truetype(FONT_PATH, font_size)

    margin = font_size // 2
    bbox = draw.textbbox((0, 0), WATERMARK_TEXT, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = img.width - text_w - margin
    y = img.height - text_h - margin

    draw.text((x + 1, y + 1), WATERMARK_TEXT, font=font, fill=(0, 0, 0, 120))
    draw.text((x, y), WATERMARK_TEXT, font=font, fill=(255, 255, 255, 160))

    return Image.alpha_composite(img, overlay).convert("RGB")


def _dms_to_decimal(dms, ref):
    degrees, minutes, seconds = (float(v) for v in dms)
    decimal = degrees + minutes / 60.0 + seconds / 3600.0
    if ref in ("S", "W"):
        decimal = -decimal
    return decimal


def read_exif_metadata(img):
    """Returns (month_name, year, (lat, lon) or None) from EXIF, before it's stripped."""
    exif = img.getexif()

    month_name, year = None, None
    try:
        exif_ifd = exif.get_ifd(0x8769)
        date_str = exif_ifd.get(36867) or exif_ifd.get(36868) or exif.get(306)
    except (KeyError, AttributeError):
        date_str = exif.get(306)

    if date_str:
        try:
            date_part = date_str.split(" ")[0]
            year_str, month_str, _ = date_part.split(":")
            year = int(year_str)
            month_name = MONTH_NAMES[int(month_str) - 1]
        except (ValueError, IndexError):
            pass

    latlon = None
    try:
        gps_ifd = exif.get_ifd(0x8825)
        if gps_ifd and 2 in gps_ifd and 4 in gps_ifd:
            lat = _dms_to_decimal(gps_ifd[2], gps_ifd.get(1, "N"))
            lon = _dms_to_decimal(gps_ifd[4], gps_ifd.get(3, "E"))
            latlon = (lat, lon)
    except (KeyError, AttributeError):
        pass

    return month_name, year, latlon


def reverse_geocode(latlon):
    if latlon is None:
        return None
    key = (round(latlon[0], 3), round(latlon[1], 3))
    if key in _geocode_cache:
        return _geocode_cache[key]

    params = urllib.parse.urlencode({
        "format": "jsonv2",
        "lat": latlon[0],
        "lon": latlon[1],
        "zoom": 10,
    })
    url = f"https://nominatim.openstreetmap.org/reverse?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "nabeel-ucsb-website/1.0"})

    location = None
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.load(resp)
        address = data.get("address", {})
        place = (
            address.get("city") or address.get("town") or address.get("village")
            or address.get("county") or address.get("state")
        )
        region = address.get("state") or address.get("country")
        if place and region and place != region:
            location = f"{place}, {region}"
        else:
            location = place or region
    except Exception as e:
        print(f"  warning: reverse geocoding failed ({e})")

    time.sleep(1)  # respect Nominatim's rate limit
    _geocode_cache[key] = location
    return location


def process(src_path, dst_path):
    img = Image.open(src_path)
    month_name, year, latlon = read_exif_metadata(img)
    location = reverse_geocode(latlon)

    img = ImageOps.exif_transpose(img)  # bake in rotation before EXIF is stripped
    img = img.convert("RGB")
    if img.width > MAX_DIMENSION or img.height > MAX_DIMENSION:
        img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)

    img = add_watermark(img)
    img.save(dst_path, "JPEG", quality=JPEG_QUALITY, optimize=True)
    print(f"wrote {dst_path} ({month_name} {year}, {location})")

    return {"month": month_name, "year": year, "location": location}


def load_existing_manifest():
    if not os.path.exists(MANIFEST_PATH):
        return {}
    text = open(MANIFEST_PATH).read()
    text = text.split("=", 1)[1].strip().rstrip(";")
    return json.loads(text)


def main(force=False):
    os.makedirs(DST_DIR, exist_ok=True)
    manifest = load_existing_manifest()

    for name in sorted(os.listdir(SRC_DIR)):
        if name.startswith("."):
            continue
        if not name.lower().endswith((".jpg", ".jpeg", ".png", ".heic")):
            continue
        src_path = os.path.join(SRC_DIR, name)
        base, _ = os.path.splitext(name)
        out_name = base + ".jpg"
        dst_path = os.path.join(DST_DIR, out_name)

        if not force and os.path.exists(dst_path) and out_name in manifest:
            continue  # already processed; preserves any manual manifest edits

        manifest[out_name] = process(src_path, dst_path)

    with open(MANIFEST_PATH, "w") as f:
        f.write("// Auto-generated by photography/process_photos.py\n")
        f.write("const photoManifest = ")
        json.dump(manifest, f, indent=2)
        f.write(";\n")
    print(f"wrote {MANIFEST_PATH}")


if __name__ == "__main__":
    import sys
    main(force="--force" in sys.argv)
