"""
Build XYZ tile pyramids from the batch delta-NBR outputs.

This script expects the GeoTIFF+PNG pairs produced by `whatisgoingon.py`
inside `data/outputs/batch_tiles/` and writes XYZ tiles under `assets/xyz/`.

Usage (from repo root):
  python srcPYTHON/make_xyz_tiles.py --zoom 6-12

The script:
- runs `gdal2tiles.py` with `--xyz` so Leaflet can read the tiles directly
- uses the colourised PNG (with its .pgw) as the source, and the matching
  GeoTIFF to get CRS + metadata
- writes a manifest JSON that you can feed to the frontend
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional
from xml.etree import ElementTree as ET

import numpy as np
import rasterio

from ThePython import delta_nbr_stats, get_latlon_bounds

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BATCH_DIR = REPO_ROOT / "data" / "outputs" / "batch_tiles"
DEFAULT_XYZ_DIR = REPO_ROOT / "assets" / "xyz"
DEFAULT_MANIFEST = DEFAULT_XYZ_DIR / "tiles_manifest.json"

# Matches both float and RGBA exports, e.g.:
# delta_nbr_p017r023_20220919_20231016.tif
# delta_nbr_p017r023_20220919_20231016_rgba.tif
FNAME_RE = re.compile(
    r"^delta_nbr_p(?P<path>\d{3})r(?P<row>\d{3})_(?P<pre>\d{8})_(?P<post>\d{8})(?P<rgba>_rgba)?\.tif$",
    re.IGNORECASE,
)


def find_gdal2tiles() -> str:
    exe = shutil.which("gdal2tiles.py")
    if not exe:
        raise RuntimeError("gdal2tiles.py not found on PATH")
    return exe


def read_zoom_from_tilemap(tilemap: Path) -> Dict[str, int]:
    """
    Parse tilemapresource.xml (written by gdal2tiles) for min/max zoom.
    """
    if not tilemap.exists():
        return {}
    try:
        root = ET.parse(tilemap).getroot()
    except Exception:
        return {}

    orders = []
    for ts in root.findall(".//TileSet"):
        try:
            orders.append(int(ts.attrib.get("order", "")))
        except (TypeError, ValueError):
            continue

    if not orders:
        return {}
    return {"minZoom": min(orders), "maxZoom": max(orders)}


def build_tiles_for_scene(
    gdal2tiles_cmd: str,
    tif_path: Path,
    src_path: Path,
    out_dir: Path,
    zoom: str,
    resampling: str = "near",
    force: bool = False,
) -> Dict[str, Optional[float]]:
    """
    Run gdal2tiles for one scene and return metadata for the manifest.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    tilemap = out_dir / "tilemapresource.xml"
    has_tiles = tilemap.exists() or any(out_dir.glob("**/*.png"))
    if has_tiles and not force:
        print(f"[skip] Tiles already exist for {tif_path.name}")
    else:
        # Use the CRS from the source GeoTIFF so the PNG (with .pgw) gets
        # a proper SRS during tiling.
        with rasterio.open(tif_path) as src:
            src_srs = src.crs.to_string() if src.crs else None

        cmd = [
            gdal2tiles_cmd,
            "--xyz",
            "-p",
            "mercator",
            "-r",
            resampling,
            "-z",
            zoom,
            "-w",
            "none",
            "-x",
            "-dstalpha",  # keep source alpha so backgrounds stay transparent
            "-srcnodata",
            "0 0 0 0",    # treat zero RGBA as transparent so black backgrounds don't burn in
        ]

        if src_srs:
            cmd.extend(["-s", src_srs])

        cmd.extend([str(src_path), str(out_dir)])

        print(f"[tile] {' '.join(cmd)}")
        subprocess.run(cmd, check=True)

    zoom_info = read_zoom_from_tilemap(tilemap)

    # Stats + bounds from the GeoTIFF (float dNBR)
    with rasterio.open(tif_path) as src:
        profile = src.profile
        data = src.read(1).astype("float32")
        nodata = src.nodata

    if nodata is not None:
        data = np.where(data == nodata, np.nan, data)

    stats = delta_nbr_stats(data)
    percent = stats.get("percent_changed")
    if percent is None or not np.isfinite(percent):
        percent = None

    min_lat, min_lon, max_lat, max_lon = get_latlon_bounds(profile)
    bounds = [[min_lat, min_lon], [max_lat, max_lon]]

    return {
        "percentChanged": percent,
        "bounds": bounds,
        **zoom_info,
    }


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Create XYZ tiles for preset scenes.")
    parser.add_argument(
        "--input-dir",
        default=str(DEFAULT_BATCH_DIR),
        help="Directory containing delta_nbr_*.tif and matching PNG/PGW.",
    )
    parser.add_argument(
        "--xyz-dir",
        default=str(DEFAULT_XYZ_DIR),
        help="Where to write XYZ tile folders (one subfolder per scene).",
    )
    parser.add_argument(
        "--manifest",
        default=str(DEFAULT_MANIFEST),
        help="Path to write manifest JSON for the frontend.",
    )
    parser.add_argument(
        "--zoom",
        default="6-12",
        help="Zoom range to pass to gdal2tiles (e.g. '5-13').",
    )
    parser.add_argument(
        "--resampling",
        default="near",
        help="Resampling method for gdal2tiles (near, bilinear, cubic, etc.).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run gdal2tiles even if the output folder already exists.",
    )

    args = parser.parse_args(argv)

    gdal2tiles_cmd = find_gdal2tiles()
    input_dir = Path(args.input_dir)
    xyz_root = Path(args.xyz_dir)
    manifest_path = Path(args.manifest)

    if not input_dir.exists():
        raise SystemExit(f"Input directory not found: {input_dir}")

    entries = []
    for tif_path in sorted(input_dir.glob("*.tif")):
        m = FNAME_RE.match(tif_path.name)
        if not m:
            print(f"[skip] Unrecognized filename pattern: {tif_path.name}")
            continue

        # Only process RGBA exports so we don't duplicate entries with the float TIFs
        if not m.group("rgba"):
            # Uncomment to see what was skipped:
            # print(f"[skip] Non-RGBA source (float dNBR): {tif_path.name}")
            continue

        path = int(m.group("path"))
        row = int(m.group("row"))
        pre_date = m.group("pre")
        post_date = m.group("post")
        is_rgba = bool(m.group("rgba"))

        tile_id = f"P{path:03d}R{row:03d}_{pre_date}_{post_date}"
        label = f"Path {path:03d} Row {row:03d} ({pre_date} vs {post_date})"

        png_name = f"delta_nbr_P{path:03d}R{row:03d}.png"
        png_path = tif_path.with_name(png_name)

        if png_path.exists():
            src_path = png_path
        elif is_rgba:
            # Fall back to the RGBA GeoTIFF itself (already colourised + alpha)
            src_path = tif_path
        else:
            print(f"[skip] PNG not found for {tile_id}: {png_path.name}")
            continue

        out_dir = xyz_root / tile_id
        meta = build_tiles_for_scene(
            gdal2tiles_cmd,
            tif_path,
            src_path,
            out_dir,
            zoom=args.zoom,
            resampling=args.resampling,
            force=args.force,
        )

        entry = {
            "id": tile_id,
            "label": label,
            "tileUrl": f"assets/xyz/{tile_id}" + "/{z}/{x}/{y}.png",
            "bounds": meta["bounds"],
            "preDate": f"{pre_date[:4]}-{pre_date[4:6]}-{pre_date[6:]}",
            "postDate": f"{post_date[:4]}-{post_date[4:6]}-{post_date[6:]}",
            "percentChanged": meta.get("percentChanged"),
        }

        if "minZoom" in meta:
            entry["minZoom"] = meta["minZoom"]
        if "maxZoom" in meta:
            entry["maxZoom"] = meta["maxZoom"]

        entries.append(entry)

    xyz_root.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(entries, indent=2))
    print(f"Wrote manifest with {len(entries)} entries -> {manifest_path}")
    print("You can paste this into the frontend or import the JSON directly.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
