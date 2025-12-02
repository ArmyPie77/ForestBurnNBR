# list_tiles_for_frontend.py
import os
import re
import json
import numpy as np
import rasterio
from pathlib import Path

from ThePython import OUTPUT_DIR, get_latlon_bounds, delta_nbr_stats

BATCH_DIR = os.path.join(OUTPUT_DIR, "batch_tiles")
REPO_ROOT = Path(__file__).resolve().parent.parent
XYZ_DIR = REPO_ROOT / "assets" / "xyz"
XYZ_MANIFEST = XYZ_DIR / "tiles_manifest.json"

# Matches:
# delta_nbr_P017R023_20220919_20231016.tif
FNAME_RE = re.compile(
    r"^delta_nbr_p(?P<path>\d{3})r(?P<row>\d{3})_(?P<pre>\d{8})_(?P<post>\d{8})\.tif$",
    re.IGNORECASE,
)

tiles = []


def load_xyz_manifest():
    if not XYZ_MANIFEST.exists():
        return {}
    try:
        data = json.loads(XYZ_MANIFEST.read_text())
    except Exception as e:
        print("Could not read XYZ manifest, continuing without it:", e)
        return {}

    lookup = {}
    for entry in data:
        tid = entry.get("id")
        if tid:
            lookup[tid] = entry
    return lookup


xyz_lookup = load_xyz_manifest()

for fname in sorted(os.listdir(BATCH_DIR)):
    if not fname.lower().endswith(".tif"):
        continue

    m = FNAME_RE.match(fname)
    if not m:
        print("Skipping unrecognized filename:", fname)
        continue

    path = int(m.group("path"))
    row = int(m.group("row"))
    pre_date = m.group("pre")
    post_date = m.group("post")

    tif_path = os.path.join(BATCH_DIR, fname)

    # Your PNGs *don’t* have dates in the name (for this batch):
    png_name = f"delta_nbr_P{path:03d}R{row:03d}.png"
    png_url = f"assets/batch_tiles/{png_name}"  # adjust if web folder differs

    with rasterio.open(tif_path) as src:
        profile = src.profile
        data = src.read(1).astype("float32")
        nodata = src.nodata

    if nodata is not None:
        data = np.where(data == nodata, np.nan, data)

    stats = delta_nbr_stats(data)  # uses threshold=0.27 unless you change it
    percent = stats.get("percent_changed")
    if percent is None or not np.isfinite(percent):
        percent = None  # avoid NaN in the UI

    # bounds: (min_lat, min_lon, max_lat, max_lon)
    min_lat, min_lon, max_lat, max_lon = get_latlon_bounds(profile)
    bounds = [[min_lat, min_lon], [max_lat, max_lon]]

    tile_id = f"P{path:03d}R{row:03d}_{pre_date}_{post_date}"
    label = f"Path {path:03d} Row {row:03d} ({pre_date} vs {post_date})"

    tile_entry = {
        "id": tile_id,
        "label": label,
        "url": png_url,
        "bounds": bounds,
        "preDate": f"{pre_date[:4]}-{pre_date[4:6]}-{pre_date[6:]}",
        "postDate": f"{post_date[:4]}-{post_date[4:6]}-{post_date[6:]}",
        "percentChanged": percent,
    }

    xyz_meta = xyz_lookup.get(tile_id)
    if xyz_meta:
        tile_entry["tileUrl"] = xyz_meta.get("tileUrl")
        if xyz_meta.get("minZoom") is not None:
            tile_entry["minZoom"] = xyz_meta["minZoom"]
        if xyz_meta.get("maxZoom") is not None:
            tile_entry["maxZoom"] = xyz_meta["maxZoom"]

    tiles.append(tile_entry)

print("const PRESET_TILES = ")
print(json.dumps(tiles, indent=2))
print(";")
