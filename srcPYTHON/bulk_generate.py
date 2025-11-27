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
    {"path": 15, "row": 22, "id": "P015R022"},
    {"path": 15, "row": 23, "id": "P015R023"},
    {"path": 15, "row": 24, "id": "P015R024"},
    {"path": 15, "row": 25, "id": "P015R025"},
    {"path": 15, "row": 26, "id": "P015R026"},
    {"path": 16, "row": 22, "id": "P016R022"},
    {"path": 16, "row": 23, "id": "P016R023"},
    {"path": 16, "row": 24, "id": "P016R024"},
    {"path": 16, "row": 25, "id": "P016R025"},
    {"path": 16, "row": 26, "id": "P016R026"},
    {"path": 17, "row": 22, "id": "P017R022"},
    {"path": 17, "row": 23, "id": "P017R023"},
    {"path": 17, "row": 24, "id": "P017R024"},
    {"path": 17, "row": 25, "id": "P017R025"},
    {"path": 17, "row": 26, "id": "P017R026"},
    {"path": 18, "row": 22, "id": "P018R022"},
    {"path": 18, "row": 23, "id": "P018R023"},
    {"path": 18, "row": 24, "id": "P018R024"},
    {"path": 18, "row": 25, "id": "P018R025"},
    {"path": 18, "row": 26, "id": "P018R026"},
]


# Date windows for the test run
# Date windows for this 2023 fires run (avoid winter; try in order until one succeeds):
# 1) PRE late 2022 → POST fall 2023
# 2) PRE spring 2023 → POST spring 2024 (fallback if no fall 2023 scene)
WINDOWS = [
    {
        "pre_start": "2022-07-15",
        "pre_end": "2022-10-31",
        "post_start": "2023-09-01",
        "post_end": "2023-10-31",
    },
    {
        "pre_start": "2023-05-01",
        "pre_end": "2023-06-15",
        "post_start": "2024-05-01",
        "post_end": "2024-06-15",
    },
]


def clean_dir(path):
    if os.path.isdir(path):
        for entry in os.listdir(path):
            full = os.path.join(path, entry)
            if os.path.isfile(full):
                os.remove(full)
            elif os.path.isdir(full):
                shutil.rmtree(full, ignore_errors=True)


def run_tile(api_key, tile):
    last_err = None
    for win in WINDOWS:
        pre_start = win["pre_start"]
        pre_end = win["pre_end"]
        post_start = win["post_start"]
        post_end = win["post_end"]
        tag = f"{tile['id'].lower()}_{pre_start.replace('-', '')}_{post_start.replace('-', '')}"
        print(f"  Trying window PRE {pre_start}→{pre_end}, POST {post_start}→{post_end}")
        try:
            res = run_delta_nbr_pipeline(
                api_key,
                pre_start, pre_end,
                post_start, post_end,
                tile["path"], tile["row"],
                tag=tag
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


def main():
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
                res = run_tile(api_key, tile)
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
