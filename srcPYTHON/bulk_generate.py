"""
Bulk generator for preloaded PNGs across multiple tiles.

Usage (from repo root):
  USAGE: python srcPYTHON/bulk_generate.py
Requires env: USGS_USERNAME, USGS_TOKEN
"""
import os
import sys
import shutil
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ThePython import (  # noqa: E402
    m2m_login,
    m2m_logout,
    run_delta_nbr_pipeline,
    DOWNLOAD_DIR,
    EXTRACT_DIR,
)

# Targeted sets — pick one at a time to keep runs light
JAMES_BAY_2023 = [
    {"path": 17, "row": 22, "id": "P017R022"},
    {"path": 17, "row": 23, "id": "P017R023"},
    {"path": 16, "row": 22, "id": "P016R022"},
    {"path": 18, "row": 22, "id": "P018R022"},  # extra James Bay coverage
]

LA_TUQUE_2020 = [
    {"path": 15, "row": 26, "id": "P015R026"},
    {"path": 15, "row": 27, "id": "P015R027"},
    {"path": 16, "row": 26, "id": "P016R026"},  # optional, north flank
]

EASTMAIN_2013 = [
    {"path": 16, "row": 22, "id": "P016R022"},
    {"path": 16, "row": 23, "id": "P016R023"},
    {"path": 17, "row": 22, "id": "P017R022"},  # optional adjacent
]

# 2023 fires focus area (western/central QC: west to ON border, north to Wiyashakimi, south below Val-d'Or, east to west side of Manicouagan)
# Break into smaller batches if desired.
TILES = [
    # paths 10–14, rows 19–26
    {"path": 10, "row": 19, "id": "P010R019"},
    {"path": 10, "row": 20, "id": "P010R020"},
    {"path": 10, "row": 21, "id": "P010R021"},
    {"path": 10, "row": 22, "id": "P010R022"},
    {"path": 10, "row": 23, "id": "P010R023"},
    {"path": 10, "row": 24, "id": "P010R024"},
    {"path": 10, "row": 25, "id": "P010R025"},
    {"path": 10, "row": 26, "id": "P010R026"},
    {"path": 11, "row": 19, "id": "P011R019"},
    {"path": 11, "row": 20, "id": "P011R020"},
    {"path": 11, "row": 21, "id": "P011R021"},
    {"path": 11, "row": 22, "id": "P011R022"},
    {"path": 11, "row": 23, "id": "P011R023"},
    {"path": 11, "row": 24, "id": "P011R024"},
    {"path": 11, "row": 25, "id": "P011R025"},
    {"path": 11, "row": 26, "id": "P011R026"},
    {"path": 12, "row": 19, "id": "P012R019"},
    {"path": 12, "row": 20, "id": "P012R020"},
    {"path": 12, "row": 21, "id": "P012R021"},
    {"path": 12, "row": 22, "id": "P012R022"},
    {"path": 12, "row": 23, "id": "P012R023"},
    {"path": 12, "row": 24, "id": "P012R024"},
    {"path": 12, "row": 25, "id": "P012R025"},
    {"path": 12, "row": 26, "id": "P012R026"},
    {"path": 13, "row": 19, "id": "P013R019"},
    {"path": 13, "row": 20, "id": "P013R020"},
    {"path": 13, "row": 21, "id": "P013R021"},
    {"path": 13, "row": 22, "id": "P013R022"},
    {"path": 13, "row": 23, "id": "P013R023"},
    {"path": 13, "row": 24, "id": "P013R024"},
    {"path": 13, "row": 25, "id": "P013R025"},
    {"path": 13, "row": 26, "id": "P013R026"},
    {"path": 13, "row": 27, "id": "P013R027"},
    {"path": 13, "row": 28, "id": "P013R028"},
    {"path": 13, "row": 29, "id": "P013R029"},
    {"path": 14, "row": 19, "id": "P014R019"},
    {"path": 14, "row": 20, "id": "P014R020"},
    {"path": 14, "row": 21, "id": "P014R021"},
    {"path": 14, "row": 22, "id": "P014R022"},
    {"path": 14, "row": 23, "id": "P014R023"},
    {"path": 14, "row": 24, "id": "P014R024"},
    {"path": 14, "row": 25, "id": "P014R025"},
    {"path": 14, "row": 26, "id": "P014R026"},
    {"path": 14, "row": 27, "id": "P014R027"},
    {"path": 14, "row": 28, "id": "P014R028"},
    {"path": 14, "row": 29, "id": "P014R029"},

    # paths 15–18, only rows 19–21 (rows 22–26 already done)
    {"path": 15, "row": 19, "id": "P015R019"},
    {"path": 15, "row": 20, "id": "P015R020"},
    {"path": 15, "row": 21, "id": "P015R021"},
    {"path": 16, "row": 19, "id": "P016R019"},
    {"path": 16, "row": 20, "id": "P016R020"},
    {"path": 16, "row": 21, "id": "P016R021"},
    {"path": 17, "row": 19, "id": "P017R019"},
    {"path": 17, "row": 20, "id": "P017R020"},
    {"path": 17, "row": 21, "id": "P017R021"},
    {"path": 18, "row": 19, "id": "P018R019"},
    {"path": 18, "row": 20, "id": "P018R020"},
    {"path": 18, "row": 21, "id": "P018R021"},

    # paths 19–20, rows 19–26
    {"path": 19, "row": 19, "id": "P019R019"},
    {"path": 19, "row": 20, "id": "P019R020"},
    {"path": 19, "row": 21, "id": "P019R021"},
    {"path": 19, "row": 22, "id": "P019R022"},
    {"path": 19, "row": 23, "id": "P019R023"},
    {"path": 19, "row": 24, "id": "P019R024"},
    {"path": 19, "row": 25, "id": "P019R025"},
    {"path": 19, "row": 26, "id": "P019R026"},
    {"path": 20, "row": 19, "id": "P020R019"},
    {"path": 20, "row": 20, "id": "P020R020"},
    {"path": 20, "row": 21, "id": "P020R021"},
    {"path": 20, "row": 22, "id": "P020R022"},
    {"path": 20, "row": 23, "id": "P020R023"},
    {"path": 20, "row": 24, "id": "P020R024"},
    {"path": 20, "row": 25, "id": "P020R025"},
    {"path": 20, "row": 26, "id": "P020R026"},
]



# Date windows (avoid winter; try all pre/post combinations until one succeeds)
# Adjust/add entries as needed.
PRE_WINDOWS = [
    {"pre_start": "2022-07-15", "pre_end": "2022-10-31"},
    {"pre_start": "2023-05-01", "pre_end": "2023-06-15"},
]

POST_WINDOWS = [
    {"post_start": "2023-09-01", "post_end": "2023-10-31"},
    {"post_start": "2024-05-01", "post_end": "2024-06-15"},
]


def clean_dir(path):
    if os.path.isdir(path):
        for entry in os.listdir(path):
            full = os.path.join(path, entry)
            if os.path.isfile(full):
                os.remove(full)
            elif os.path.isdir(full):
                shutil.rmtree(full, ignore_errors=True)


def run_tile(api_key, tile, make_png=False, make_rgba=True):
    last_err = None
    for pre in PRE_WINDOWS:
        for post in POST_WINDOWS:
            pre_start = pre["pre_start"]
            pre_end = pre["pre_end"]
            post_start = post["post_start"]
            post_end = post["post_end"]
            tag = f"{tile['id'].lower()}_{pre_start.replace('-', '')}_{post_start.replace('-', '')}"
            print(f"  Trying PRE {pre_start}→{pre_end}, POST {post_start}→{post_end}")
            try:
                res = run_delta_nbr_pipeline(
                    api_key,
                    pre_start, pre_end,
                    post_start, post_end,
                    tile["path"], tile["row"],
                    tag=tag,
                    make_png=make_png,
                    make_rgba=make_rgba
                )
                # Echo bounds to paste into map.js
                b = res.get("bounds")
                if b:
                    min_lat, min_lon, max_lat, max_lon = b
                    print(f"  Bounds for {tag}: [[{min_lat}, {min_lon}], [{max_lat}, {max_lon}]]")
                return res
            except Exception as e:
                last_err = e
                print(f"  Window failed: {e}")
                continue
    # If all windows fail, raise the last error
    raise last_err if last_err else RuntimeError("No windows attempted")


def main(make_png=False, make_rgba=True):
    username = os.environ.get("USGS_USERNAME")
    token = os.environ.get("USGS_TOKEN")
    if not username or not token:
        raise RuntimeError("USGS_USERNAME / USGS_TOKEN not set")

    api_key = m2m_login(username, token)
    successes = []
    failures = []

    try:
        for tile in TILES:
            print(f"Processing {tile['id']}...")
            try:
                res = run_tile(api_key, tile, make_png=make_png, make_rgba=make_rgba)
                successes.append(res)
            except Exception as e:
                failures.append({"tile": tile, "error": str(e)})
                print(f"Failed {tile['id']}: {e}")
            finally:
                clean_dir(DOWNLOAD_DIR)
                clean_dir(EXTRACT_DIR)
    finally:
        m2m_logout(api_key)

    print("\nDone.")
    print(f"Successes: {len(successes)}")
    print(f"Failures: {len(failures)}")
    if failures:
        for f in failures:
            t = f["tile"]
            print(f"  {t['id']} -> {f['error']}")


if __name__ == "__main__":
    main()
