"""
Thin wrapper around `gdal2tiles.py` to create XYZ tiles from a GeoTIFF.

Example:
  python srcPYTHON/gdal2tiles_runner.py \
    --input data/outputs/delta_nbr_rgba.tif \
    --out-root assets/xyz \
    --zoom 6-12 \
    --srcnodata 0 0 0 0

Notes:
- Assumes your input GeoTIFF already looks the way you want (e.g., RGBA with
  transparency). If you only have float dNBR, colorize it first.
- Leaves your existing PNG overlays untouched; this is just an alternate path.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


def find_gdal2tiles() -> str:
    path = shutil.which("gdal2tiles.py")
    if not path:
        raise SystemExit("gdal2tiles.py not found on PATH. Install GDAL or add it to PATH.")
    return path


def build_tile_command(args, gdal2tiles_path: str) -> list[str]:
    cmd = [
        gdal2tiles_path,
        "--xyz",
        "-p",
        "mercator",
        "-r",
        args.resampling,
        "-z",
        args.zoom,
        "-w",
        "none",
        "-x",
        "-dstalpha",
    ]

    if args.srcnodata:
        # gdal2tiles expects a single nodata argument; join if multiple tokens were provided
        srcnodata_val = " ".join(args.srcnodata)
        cmd.extend(["-srcnodata", srcnodata_val])

    cmd.extend([str(args.input), str(args.output)])
    return cmd


def main() -> int:
    parser = argparse.ArgumentParser(description="Run gdal2tiles.py for one GeoTIFF.")
    parser.add_argument("--input", required=True, type=Path, help="Input GeoTIFF (already colorized/alpha).")
    parser.add_argument(
        "--out-root",
        default="assets/xyz",
        type=Path,
        help="Root folder to place XYZ tiles (will create subfolder from input stem).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional explicit output folder. Default: <out-root>/<input-stem>",
    )
    parser.add_argument(
        "--zoom",
        default="6-12",
        help="Zoom range, e.g. '5-13'.",
    )
    parser.add_argument(
        "--resampling",
        default="near",
        help="Resampling method (near, bilinear, cubic, etc.).",
    )
    parser.add_argument(
        "--srcnodata",
        nargs="+",
        help="Values to treat as nodata, e.g. '-srcnodata 0 0 0 0' for RGBA.",
    )

    args = parser.parse_args()

    if not args.input.exists():
        raise SystemExit(f"Input file not found: {args.input}")

    gdal2tiles_path = find_gdal2tiles()

    out_dir = args.output if args.output else args.out_root / args.input.stem
    out_dir.mkdir(parents=True, exist_ok=True)

    cmd = build_tile_command(args, gdal2tiles_path)
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print("Tiles written to", out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
