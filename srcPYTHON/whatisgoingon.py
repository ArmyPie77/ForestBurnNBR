import os
import numpy as np
import rasterio

from ThePython import (
    m2m_login,
    m2m_logout,
    download_landsat_period,
    process_landsat,
    export_png_from_tif,
    OUTPUT_DIR,
    export_burn_png_from_delta,
)


def get_landsat_date_from_band_path(band_path: str) -> str:
    """
    Extract the acquisition date (YYYYMMDD) from a Landsat band filename.
    Example:
      LC08_L2SP_010026_20220918_20220928_02_T1_SR_B5.TIF
                       ^^^^^^^^  this one
    """
    base = os.path.basename(band_path)
    parts = base.split("_")
    # expect something like LC08_L2SP_010026_20220918_20220928_02_T1_SR_B5.TIF
    if len(parts) >= 4 and parts[3].isdigit() and len(parts[3]) == 8:
        return parts[3]  # e.g. "20220918"
    return "unknowndate"


# ---- fixed date ranges (same as your interactive run) ----
PRE_START = "2022-05-25"
PRE_END   = "2022-07-01"
POST_START = "2023-08-15"
POST_END   = "2023-10-17"

USERNAME = "Matt2icy"
APP_TOKEN = "cir0gHyF3eH89ARS4sI9sFcQT_31qZg@B1hhIby!D3@tF@S7kuT3TzLc1SroNjb8"

def run_batch():
    api_key = m2m_login(USERNAME, APP_TOKEN)

    # put all batch PNGs/TIFs in one subfolder
    batch_dir = os.path.join(OUTPUT_DIR, "batch_tiles")
    os.makedirs(batch_dir, exist_ok=True)
    print("Batch outputs will go in:", batch_dir)

    for path in range(17, 18):   # 10..20 inclusive
        for row in range(15, 31):  # 15..30 inclusive
            print(f"\n=== Processing path {path:03d}, row {row:03d} ===")

            # 1) download pre + post bands
            try:
                pre_bands = download_landsat_period(
                    api_key, PRE_START, PRE_END, path, row
                )
                post_bands = download_landsat_period(
                    api_key, POST_START, POST_END, path, row
                )
            except Exception as e:
                print(f"Failed for {path:03d}/{row:03d} while downloading: {e}")
                continue

            # --- NEW: extract actual acquisition dates from filenames ---
            pre_date = get_landsat_date_from_band_path(pre_bands["nir"])
            post_date = get_landsat_date_from_band_path(post_bands["nir"])
            # e.g. "20220918", "20231016" or "unknowndate" if parsing fails

            # 2) run delta NBR pipeline
            try:
                nbr_pre, nbr_post, delta, out_profile = process_landsat(
                    pre_bands["nir"], pre_bands["swir"],
                    post_bands["nir"], post_bands["swir"],
                    pre_bands["qa"],  post_bands["qa"],
                )
            except Exception as e:
                print(f"process_landsat failed for {path:03d}/{row:03d}: {e}")
                continue

            # 3) write tile-specific GeoTIFF
            tif_name = f"delta_nbr_P{path:03d}R{row:03d}_{pre_date}_{post_date}.tif"
            tif_path = os.path.join(batch_dir, tif_name)

            out_profile = out_profile.copy()
            out_profile.update({
                "driver": "GTiff",
                "dtype": "float32",
                "count": 1,
                "nodata": -9999.0,
            })

            delta_to_write = np.where(
                np.isnan(delta),
                out_profile["nodata"],
                delta
            ).astype("float32")

            with rasterio.open(tif_path, "w", **out_profile) as dst:
                dst.write(delta_to_write, 1)

            print("  Wrote TIF:", tif_path)

            # 4) export PNG for web
            # 4) export PNG for web (burn-only, transparent background)
            png_name = f"delta_nbr_P{path:03d}R{row:03d}.png"
            png_path = os.path.join(batch_dir, png_name)

            export_burn_png_from_delta(tif_path, png_path)
            print("  Wrote burn-only PNG:", png_path)


    m2m_logout(api_key)


if __name__ == "__main__":
    run_batch()
