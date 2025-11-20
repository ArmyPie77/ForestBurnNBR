
import numpy as np
from pyproj import Transformer
import os
import rasterio
from pyproj import Transformer
from rasterio.warp import reproject, Resampling
import matplotlib.pyplot as plt
import tarfile
import glob
import requests
from botocore import UNSIGNED
from botocore.config import Config
import json
from rasterio.transform import array_bounds
import time
from rasterio.transform import xy

BASE_DIR = os.path.join(os.getcwd(), "data")  
DOWNLOAD_DIR = os.path.join(BASE_DIR, "dataAPI")
EXTRACT_DIR = os.path.join(DOWNLOAD_DIR, "extracted")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(EXTRACT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

DELTA_NBR_THRESHOLD = 0.1
MAX_CLOUD_COVER = 15



#this code below is a function for loading the bands, it loads a single landsat .tif. band_path is the path to the .tif, 
def load_band(band_path):
    #Load a single band from a GeoTIFF
    with rasterio.open(band_path) as src:
        arr = src.read(1).astype('float32')

        profile = src.profile
    return arr, profile



#this is my load cloud/QA mask function, took me a while to realise that its not just 0 is cloud and 1 is clear skies, but instead theres a system of bits to represent differnet visual obstructions . QA is the cloud band stuff
def load_cloud_mask(qa_path):
    with rasterio.open(qa_path) as src:
        qa = src.read(1)

    FILL    = 0
    DILATED = 1
    CIRRUS  = 2
    CLOUD   = 3
    SHADOW  = 4
    SNOW    = 5

    mask = (
        ((qa & (1 << FILL))    != 0) |
        ((qa & (1 << DILATED)) != 0) |
        ((qa & (1 << CIRRUS))  != 0) |
        ((qa & (1 << CLOUD))   != 0) |
        ((qa & (1 << SHADOW))  != 0) |
        ((qa & (1 << SNOW))    != 0)
    )

    return mask


#ok now for raster alignment. it aligns the source to the target projection and location. i need rasterio

def align_raster(source_arr, source_profile, target_profile):
    dst_arr = np.empty((target_profile['height'], target_profile['width']), dtype=np.float32) #making an empty array to hold the reprojected raster, size maatches target raster
    reproject(
        source=source_arr, #2d array of the raster i want to reporject (eg post fire NIR)
        destination=dst_arr, #where aligned pixels will go 
        src_transform=source_profile['transform'], #metadata from source raster (size and whatnot)
        src_crs=source_profile['crs'], #tells rasterio how source pixels are atm 
        dst_transform=target_profile['transform'], #metadata from target of what grid/coord system we want from the target raster
        dst_crs=target_profile['crs'],
        resampling=Resampling.bilinear #interpolations for fractional pizel shifts 
    )
    return dst_arr



#ok now to realign the masks which have been  done by aligning a boolean mask to a target raster using neareast neighbour resampling 
def align_mask(mask_source, source_profile, target_profile):
   
    dst_mask = np.empty((target_profile['height'], target_profile['width']), dtype=np.uint8)
    
    reproject(
        source=mask_source.astype(np.uint8),  # turn to integer for resampling
        destination=dst_mask,
        src_transform=source_profile['transform'],
        src_crs=source_profile['crs'],
        dst_transform=target_profile['transform'],
        dst_crs=target_profile['crs'],
        resampling=Resampling.nearest     # nearest preserves 0/1 exactly
    )
    
    return dst_mask.astype(bool)


#ok now time to compute the NBR function
def compute_nbr(nir, swir2, mask=None):
    denom = nir + swir2
    with np.errstate(divide="ignore", invalid="ignore"):
        nbr = (nir - swir2) / denom
    # force denom==0 to NaN
    nbr[denom == 0] = np.nan
    if mask is not None:
        nbr = np.where(mask, np.nan, nbr)
    return nbr


#now i calculate delta nbr (change)
def compute_delta_nbr(nbr_pre, nbr_post):
    return nbr_pre - nbr_post


#this one calculates the stats of change from deltaNBR 
def delta_nbr_stats(delta, threshold=0.27): #0.27 is the deltanbr threshold i will use to determain if a bit of land has been sufficiantly destroyed for me to concider it to be burnt
    valid = ~np.isnan(delta)
    changed = (delta >= threshold) & valid
    percent_changed = np.nansum(changed) / np.count_nonzero(valid) * 100
    return {
        'valid_pixels': int(np.count_nonzero(valid)),
        'changed_pixels': int(np.count_nonzero(changed)),
        'percent_changed': percent_changed
    } #this returns a dictonary with number of pixels that are valid(not masked), number of pixels above burn threshold, %changed is percent of valid pixels above burn threshold 


def classify_dnbr(delta):
    """
    Classify dNBR into USGS burn severity classes.

    Returns uint8 array with codes:
      0 = nodata / background
      1 = Enhanced regrowth, high
      2 = Enhanced regrowth, low
      3 = Unburned
      4 = Low severity
      5 = Moderate-low severity
      6 = Moderate-high severity
      7 = High severity
    """
    classes = np.zeros(delta.shape, dtype=np.uint8)

    valid = np.isfinite(delta)
    d = np.where(valid, delta, np.nan)

    # ranges from the table (not scaled)
    # Enhanced regrowth, high
    classes[(d >= -0.500) & (d <= -0.251)] = 1
    # Enhanced regrowth, low
    classes[(d >  -0.250) & (d <= -0.101)] = 2
    # Unburned
    classes[(d >  -0.100) & (d <=  0.099)] = 3
    # Low severity
    classes[(d >=  0.100) & (d <=  0.269)] = 4
    # Moderate-low severity
    classes[(d >=  0.270) & (d <=  0.439)] = 5
    # Moderate-high severity
    classes[(d >=  0.440) & (d <=  0.659)] = 6
    # High severity
    classes[(d >=  0.660) & (d <=  1.300)] = 7

    # any NaN stays 0 (background)
    return classes

from matplotlib.colors import ListedColormap

def export_dnbr_class_png(tif_path, png_path):
    """
    Read a dNBR GeoTIFF, classify it using USGS burn severity
    classes, and write a PNG with the USGS-like color scheme,
    plus a PNG world file.
    """
    with rasterio.open(tif_path) as src:
        data = src.read(1).astype("float32")
        transform = src.transform
        nodata = src.nodata

    # Turn nodata to NaN
    if nodata is not None:
        data = np.where(data == nodata, np.nan, data)

    # Classify to 0–7
    classes = classify_dnbr(data)

    # Colors approximating the USGS table
    # 0: background (black)
    # 1: dark olive (enhanced regrowth, high)
    # 2: light olive (enhanced regrowth, low)
    # 3: bright green (unburned)
    # 4: yellow (low severity)
    # 5: orange (moderate-low)
    # 6: red-orange (moderate-high)
    # 7: purple (high severity)
    cmap = ListedColormap([
        (0/255,   0/255,   0/255),    # 0
        (122/255, 135/255, 55/255),   # 1
        (172/255, 190/255, 77/255),   # 2
        (0/255,   203/255, 0/255),    # 3
        (255/255, 255/255, 0/255),    # 4
        (245/255, 107/255, 0/255),    # 5
        (230/255, 55/255,  0/255),    # 6
        (122/255, 1/255,   119/255),  # 7
    ])

    # Save PNG: classes are 0–7, use discrete cmap
    plt.imsave(png_path, classes, cmap=cmap, vmin=0, vmax=7)

    # World file (.pgw) so it’s georeferenced
    pixel_width = transform.a
    pixel_height = transform.e
    x_ul, y_ul = xy(transform, 0, 0, offset="center")

    worldfile_path = os.path.splitext(png_path)[0] + ".pgw"
    with open(worldfile_path, "w") as f:
        f.write(f"{pixel_width}\n")
        f.write("0.0\n")
        f.write("0.0\n")
        f.write(f"{pixel_height}\n")
        f.write(f"{x_ul}\n")
        f.write(f"{y_ul}\n")

    print("Wrote PNG:", png_path)
    print("Wrote world file:", worldfile_path)



#this function is to get the landsatexplorer api to seearch for the images i want so i dont have to get my data from the website and manually put in my files in my code. i have to use my own password and username for earthexplorer


WRS2_BBOX = {
    (18, 24): (-116.123, 36.789, -114.456, 38.012),
    (13, 32): (-120.321, 39.123, -118.654, 40.456),
    # manually adding in the bounds of different path/rows, i will add all the ones for quebec but for now ill just do the two for testing 
}

def wrs2_to_bbox(path, row):
    return WRS2_BBOX.get((path, row))

# cir0gHyF3eH89ARS4sI9sFcQT_31qZg@B1hhIby!D3@tF@S7kuT3TzLc1SroNjb8


SERVICE_URL = "https://m2m.cr.usgs.gov/api/api/json/stable/"

def m2m_login(username, app_token):
    """
    Logs in to USGS M2M using login-token and returns the API key.
    Mirrors the official example script.
    """
    url = SERVICE_URL + "login-token"
    payload = {"username": username, "token": app_token}
    json_data = json.dumps(payload)

    resp = requests.post(url, json_data)
    if resp is None:
        raise RuntimeError("No output from service")

    try:
        output = resp.json()
    except Exception as e:
        raise RuntimeError(f"Failed to parse login-token JSON: {e}\nRaw: {resp.text}")

    if output.get("errorCode") is not None:
        raise RuntimeError(
            f"Login failed: {output['errorCode']} - {output.get('errorMessage')}"
        )

    api_key = output["data"]
    print("Authenticated. API key:", api_key)
    return api_key



def m2m_search(api_key, bbox, start, end):
    """
    Scene-search for landsat_ot_c2_l2 over an MBR bbox and date range.
    bbox = (min_lon, min_lat, max_lon, max_lat)
    """
    url = SERVICE_URL + "scene-search"
    headers = {"X-Auth-Token": api_key}

    min_lon, min_lat, max_lon, max_lat = bbox

    spatial_filter = {
        "filterType": "mbr",
        "lowerLeft": {"latitude": min_lat, "longitude": min_lon},
        "upperRight": {"latitude": max_lat, "longitude": max_lon},
    }

    acquisition_filter = {
        "start": start,
        "end": end,
    }

    # Optional cloud filter using your global MAX_CLOUD_COVER
    cloud_cover_filter = {
        "min": 0,
        "max": MAX_CLOUD_COVER,
        "includeUnknown": False,
    }

    scene_filter = {
        "spatialFilter": spatial_filter,
        "acquisitionFilter": acquisition_filter,
        "cloudCoverFilter": cloud_cover_filter,
    }

    payload = {
        "datasetName": "landsat_ot_c2_l2",
        "sceneFilter": scene_filter,
        "maxResults": 5,
    }

    resp = requests.post(url, headers=headers, json=payload)

    if resp.status_code != 200:
        print("scene-search HTTP status:", resp.status_code)
        print("scene-search response text:", resp.text)
    resp.raise_for_status()

    data = resp.json()
    if data.get("errorCode"):
        raise Exception(
            f"scene-search failed: {data['errorCode']} {data.get('errorMessage')}"
        )

    return data["data"]["results"]






def download_to_file(url, out_path):
    r = requests.get(url, stream=True)
    r.raise_for_status()
    with open(out_path, "wb") as f:
        for chunk in r.iter_content(1024 * 1024):
            f.write(chunk)
    return out_path

"""
def m2m_search_wrs2(api_key, path, row, start, end):
    
   # Scene-search for landsat_ot_c2_l2 using WRS-2 path/row instead of an MBR.
   # This should match exactly what EarthExplorer does.
    
    url = SERVICE_URL + "scene-search"
    headers = {"X-Auth-Token": api_key}

    spatial_filter = {
        "filterType": "wrs2",
        "path": path,
        "row": row
    }

    acquisition_filter = {
        "start": start,
        "end": end
    }

    scene_filter = {
        "spatialFilter": spatial_filter,
        "acquisitionFilter": acquisition_filter
    }

    payload = {
        "datasetName": "landsat_ot_c2_l2",
        "sceneFilter": scene_filter,
        "maxResults": 5
    }

    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code != 200:
        print("scene-search HTTP status:", resp.status_code)
        print("scene-search response text:", resp.text)
    resp.raise_for_status()

    data = resp.json()
    if data.get("errorCode"):
        raise Exception(
            f"scene-search failed: {data['errorCode']} {data.get('errorMessage')}"
        )

    return data["data"]["results"]
"""

#this is for automated coord conversion 


SERVICE_URL = "https://m2m.cr.usgs.gov/api/api/json/stable/"

def _m2m_get_products_for_scene(api_key, scene):
    """
    Call download-options and return the list of product dicts for this scene.
    """
    headers = {"X-Auth-Token": api_key}
    url = SERVICE_URL + "download-options"
    payload = {
        "datasetName": "landsat_ot_c2_l2",
        "entityIds": [scene["entityId"]],
    }
    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    out = resp.json()

    if out.get("errorCode"):
        raise RuntimeError(f"download-options failed: {out['errorCode']} {out.get('errorMessage')}")

    root = out.get("data")
    if root is None:
        raise RuntimeError("download-options returned data = null")

    # Typical case: data is a list of product dicts
    if isinstance(root, list):
        products = root
    # Some APIs wrap them, keep this as a fallback
    elif isinstance(root, dict) and "downloadOptions" in root:
        products = root["downloadOptions"]
    else:
        raise RuntimeError(f"Unexpected download-options structure: {type(root)}")

    if not products:
        raise RuntimeError("No products returned by download-options")

    # Debug: see what products exist (first time you run this, read the console)
    print("download-options products (truncated):")
    for p in products:
        print(json.dumps({
            "id": p.get("id"),
            "productName": p.get("productName"),
            "label": p.get("label"),
            "available": p.get("available"),
        }, indent=2))

    return products


def _pick_sr_bundle_product(products):
    """
    Heuristically pick the Surface Reflectance Level-2 bundle product.
    """
    def pname(p):
        return (p.get("productName") or p.get("label") or "").upper()

    # Prefer things that clearly look like SR / Level-2
    sr_candidates = [
        p for p in products
        if "SURFACE REFLECTANCE" in pname(p)
        or "SR" in pname(p)
        or "L2SP" in pname(p)
    ]

    if sr_candidates:
        bundle = sr_candidates[0]
    else:
        # Fallback: just take first available product
        bundle = next((p for p in products if p.get("available", True)), products[0])

    print("Chosen bundle product:", json.dumps({
        "id": bundle.get("id"),
        "productName": bundle.get("productName"),
        "label": bundle.get("label")
    }, indent=2))

    return bundle


def _download_bundle_for_scene(api_key, scene, product):
    """
    Use download-request (+ download-retrieve if needed) to download
    the chosen bundle product. Returns path to the downloaded file.
    """
    headers = {"X-Auth-Token": api_key}

    # ---- download-request ----
    req_url = SERVICE_URL + "download-request"
    label = f"bundle_{scene['entityId']}"

    req_payload = {
        "downloads": [{
            "entityId": scene["entityId"],
            "productId": product["id"]
        }],
        "label": label
    }

    resp = requests.post(req_url, headers=headers, json=req_payload)
    resp.raise_for_status()
    dr = resp.json()

    if dr.get("errorCode"):
        raise RuntimeError(f"download-request failed: {dr['errorCode']} {dr.get('errorMessage')}")

    data = dr["data"]

    urls = []
    if data.get("availableDownloads"):
        urls = [d["url"] for d in data["availableDownloads"] if d.get("url")]

    # If not ready, call download-retrieve a few times
    if not urls and data.get("preparingDownloads"):
        retrieve_url = SERVICE_URL + "download-retrieve"
        retrieve_payload = {"label": data.get("label", label)}

        for _ in range(5):
            print("Waiting for bundle to become available...")
            time.sleep(10)
            resp2 = requests.post(retrieve_url, headers=headers, json=retrieve_payload)
            resp2.raise_for_status()
            dr2 = resp2.json()
            if dr2.get("errorCode"):
                raise RuntimeError(f"download-retrieve failed: {dr2['errorCode']} {dr2.get('errorMessage')}")

            d2 = dr2["data"]
            urls = [d["url"] for d in d2.get("available", []) if d.get("url")]
            if urls:
                break

    if not urls:
        raise RuntimeError("Could not get a download URL for the bundle product")

    bundle_url = urls[0]
    print("Bundle download URL:", bundle_url)

    # Local bundle filename (let extension follow the URL)
    filename = os.path.basename(bundle_url.split("?")[0])
    if not filename:
        filename = f"{scene['displayId']}_bundle.tar"

    local_path = os.path.join(DOWNLOAD_DIR, filename)
    print(f"Downloading bundle to {local_path}")
    download_to_file(bundle_url, local_path)
    return local_path


def _extract_landsat_bands_from_bundle(bundle_path):
    """
    Open the bundle (tar) and extract SR_B5, SR_B7, QA_PIXEL
    into EXTRACT_DIR. Returns dict with local paths.
    """
    # Only tar support here; if you ever get zip, we can add zipfile logic
    if not tarfile.is_tarfile(bundle_path):
        raise RuntimeError(f"Bundle is not a tar file: {bundle_path}")

    bands = {"nir": None, "swir": None, "qa": None}

    with tarfile.open(bundle_path, "r") as tf:
        members = tf.getmembers()

        nir_member = None
        swir_member = None
        qa_member = None

        for m in members:
            name = m.name.upper()
            if name.endswith("SR_B5.TIF"):
                nir_member = m
            elif name.endswith("SR_B7.TIF"):
                swir_member = m
            elif "QA_PIXEL.TIF" in name:
                qa_member = m

        # Extract the members we found
        os.makedirs(EXTRACT_DIR, exist_ok=True)

        def extract_member(member):
            tf.extract(member, EXTRACT_DIR)
            return os.path.join(EXTRACT_DIR, member.name)

        if nir_member:
            bands["nir"] = extract_member(nir_member)
        if swir_member:
            bands["swir"] = extract_member(swir_member)
        if qa_member:
            bands["qa"] = extract_member(qa_member)

    print("Extracted bands from bundle:", bands)

    missing = [k for k, v in bands.items() if v is None]
    if missing:
        raise RuntimeError(f"Bundle did not contain expected files for: {', '.join(missing)}")

    return bands



def m2m_get_band_urls(api_key, scene):
    """
    High-level helper:
      - get products for scene
      - pick SR bundle product
      - download bundle
      - extract SR_B5, SR_B7, QA_PIXEL

    Returns local file paths for the three bands. it also checks if its already downloaded so it doesnt have to again 
    """
    scene_id = scene["displayId"]  # e.g. LC08_L2SP_010026_20220918_20220928_02_T1

    nir_path  = os.path.join(EXTRACT_DIR, f"{scene_id}_SR_B5.TIF")
    swir_path = os.path.join(EXTRACT_DIR, f"{scene_id}_SR_B7.TIF")
    qa_path   = os.path.join(EXTRACT_DIR, f"{scene_id}_QA_PIXEL.TIF")

    # If we've already extracted them, reuse
    if all(os.path.exists(p) for p in [nir_path, swir_path, qa_path]):
        return {"nir": nir_path, "swir": swir_path, "qa": qa_path}

    # Otherwise fall back to the full flow (request + download + extract)
    products = _m2m_get_products_for_scene(api_key, scene)
    bundle_product = _pick_sr_bundle_product(products)
    bundle_path = _download_bundle_for_scene(api_key, scene, bundle_product)
    bands = _extract_landsat_bands_from_bundle(bundle_path)
    return bands


def _scene_path_row_from_metadata(scene):
    """
    Extract WRS path/row as integers from the scene['metadata'] list.
    Returns (path, row) or (None, None) if not found.
    """
    md = scene.get("metadata")
    path_val = None
    row_val = None

    if isinstance(md, dict):
        for key in ("WRS_PATH", "WRS Path", "Path"):
            if key in md:
                try:
                    path_val = int(str(md[key]).strip())
                    break
                except ValueError:
                    pass
        for key in ("WRS_ROW", "WRS Row", "Row"):
            if key in md:
                try:
                    row_val = int(str(md[key]).strip())
                    break
                except ValueError:
                    pass

    elif isinstance(md, list):
        for item in md:
            if not isinstance(item, dict):
                continue
            fname = str(item.get("fieldName", "")).strip()
            val = item.get("value", "")
            if fname in ("WRS_PATH", "WRS Path", "Path"):
                try:
                    path_val = int(str(val).strip())
                except ValueError:
                    pass
            if fname in ("WRS_ROW", "WRS Row", "Row"):
                try:
                    row_val = int(str(val).strip())
                except ValueError:
                    pass

    return path_val, row_val

import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import Normalize

# ... your existing code ...

def export_burn_png_from_delta(tif_path, png_path, threshold=DELTA_NBR_THRESHOLD):
    """
    Create a PNG where only pixels with delta NBR >= threshold
    are visible (coloured). Everything else is fully transparent.

    This is meant specifically for delta-NBR rasters.
    """
    with rasterio.open(tif_path) as src:
        data = src.read(1).astype("float32")
        transform = src.transform
        nodata = src.nodata

        # Mask nodata to NaN
        if nodata is not None:
            data = np.where(data == nodata, np.nan, data)

        # Burned = above threshold
        burned = (data >= threshold) & np.isfinite(data)

        # If literally nothing is burned, just make a fully transparent PNG
        if not np.any(burned):
            h, w = data.shape
            rgba = np.zeros((h, w, 4), dtype=np.float32)
        else:
            # Normalise only over burned pixels so the colours use a sensible range
            vmin = threshold
            vmax = np.nanpercentile(data[burned], 99)
            if vmin == vmax:
                vmax = vmin + 0.01

            norm = Normalize(vmin=vmin, vmax=vmax, clip=True)
            cmap = cm.get_cmap("inferno")

            # Start with fully transparent
            h, w = data.shape
            rgba = np.zeros((h, w, 4), dtype=np.float32)

            # Apply colormap only to burned pixels
            normed_vals = norm(data[burned])
            colors = cmap(normed_vals)  # returns RGBA in [0,1]

            rgba[burned] = colors
            # Force alpha = 1 for burned pixels (opaque)
            rgba[burned, 3] = 1.0

        # Save PNG
        plt.imsave(png_path, rgba)

    # ----- Write a PNG world file (.pgw) for location -----
    pixel_width = transform.a
    pixel_height = transform.e  # usually negative

    from rasterio.transform import xy
    x_ul, y_ul = xy(transform, 0, 0, offset="center")

    worldfile_path = os.path.splitext(png_path)[0] + ".pgw"
    with open(worldfile_path, "w") as f:
        f.write(f"{pixel_width}\n")  # pixel size in X
        f.write("0.0\n")             # rotation about Y
        f.write("0.0\n")             # rotation about X
        f.write(f"{pixel_height}\n") # pixel size in Y
        f.write(f"{x_ul}\n")         # X of UL pixel centre
        f.write(f"{y_ul}\n")         # Y of UL pixel centre

    print("Wrote burn-only PNG:", png_path)
    print("Wrote world file:", worldfile_path)




def download_landsat_period(api_key, start_date, end_date, path, row):
    """
    Given WRS-2 path/row + date range:
      - Get bbox (from WRS2_BBOX or grid2ll)
      - Run scene-search over that bbox + date
      - Filter to exact WRS path/row
      - Pick the least cloudy scene
      - Download SR bundle, extract SR_B5, SR_B7, QA_PIXEL

    Returns: dict with local file paths:
      {
        "nir":  "...SR_B5.TIF",
        "swir": "...SR_B7.TIF",
        "qa":   "...QA_PIXEL.TIF"
      }
    """
    # ---- 1) Path/row -> bbox (min_lon, min_lat, max_lon, max_lat) ----
    bbox = wrs2_to_bbox(path, row)
    if bbox is None:
        print(f"No bounding box in WRS2_BBOX for path {path}, row {row}, asking M2M grid2ll...")
        bbox = wrs2_to_bbox_api(api_key, path, row)

    min_lon, min_lat, max_lon, max_lat = bbox
    print("Using bbox:", bbox)

    # ---- 2) Scene-search over that bbox + date range ----
    scenes = m2m_search(api_key, bbox, start_date, end_date)

    if not scenes:
        raise Exception(
            f"No scenes found between {start_date} and {end_date} for bbox {bbox}"
        )

    # ---- Filter to exact WRS path/row from metadata ----
    exact_scenes = []
    for s in scenes:
        p, r = _scene_path_row_from_metadata(s)
        if p == path and r == row:
            exact_scenes.append(s)

    if exact_scenes:
        print(f"Filtered to {len(exact_scenes)} scenes with WRS {path:03d}/{row:03d}")
        scenes = exact_scenes
    else:
        print("WARNING: no scenes matched exact WRS path/row in metadata.")
        print("         Using all scenes returned for the bbox (may include neighbors).")

    # ---- Prefer the least cloudy scene ----
    def scene_cloud(s):
        md = s.get("metadata")

        # dict-style
        if isinstance(md, dict):
            try:
                return float(md.get("cloudCoverFull",
                                    md.get("cloudCover", 9999)))
            except (TypeError, ValueError):
                return 9999.0

        # list-style
        if isinstance(md, list):
            val = 9999.0
            for item in md:
                if not isinstance(item, dict):
                    continue
                name = str(item.get("fieldName", "")).strip().lower()
                v = item.get("value", "")
                if name in (
                    "cloudcoverfull",
                    "cloudcover",
                    "cloud_cover",
                    "scene cloud cover l1",
                ):
                    if isinstance(v, str):
                        v = v.replace("percent", "").strip()
                    try:
                        val = float(v)
                    except (TypeError, ValueError):
                        pass
            return val

        return 9999.0

    scenes_sorted = sorted(scenes, key=scene_cloud)
    scene = scenes_sorted[0]

    print("Chosen scene:", scene["displayId"])
    print("  WRS from metadata:", _scene_path_row_from_metadata(scene))
    print("  Cloud cover (if available):", scene_cloud(scene))

    # ---- 3) Download bundle + extract bands ----
    band_paths = m2m_get_band_urls(api_key, scene)
    print("Band paths:", band_paths)

    if not band_paths:
        raise Exception("No band paths found for scene")

    # ---- 4) Return dict of file paths ----
    return band_paths














def wrs2_to_bbox_api(api_key, path, row):
    """
    Use M2M grid2ll to convert WRS-2 path/row to
    (min_lon, min_lat, max_lon, max_lat) in WGS84.
    Handles several coordinate formats.
    """
    url = SERVICE_URL + "grid2ll"
    headers = {"X-Auth-Token": api_key}
    payload = {
        "gridType": "WRS2",
        "path": f"{path:03d}",
        "row": f"{row:03d}",
        "responseShape": "polygon"
    }

    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code != 200:
        print("grid2ll HTTP status:", resp.status_code)
        print("grid2ll response:", resp.text)
    resp.raise_for_status()

    out = resp.json()
    if out.get("errorCode"):
        raise RuntimeError(
            f"grid2ll failed: {out['errorCode']} - {out.get('errorMessage')}"
        )

    data = out["data"]
    coords = data.get("coordinates")
    if coords is None:
        raise RuntimeError(f"grid2ll: unexpected data structure, no 'coordinates': {data}")

    # Case 1: list of dicts [{latitude:..., longitude:...}, ...]
    if coords and isinstance(coords[0], dict) and "latitude" in coords[0]:
        lats = [pt["latitude"] for pt in coords]
        lons = [pt["longitude"] for pt in coords]

    # Case 2: [[lon, lat], [lon, lat], ...]
    elif coords and isinstance(coords[0], list) and isinstance(coords[0][0], (float, int)):
        ring = coords
        lons = [pt[0] for pt in ring]
        lats = [pt[1] for pt in ring]

    # Case 3: [[[lon, lat], ...], ...] – multi-ring polygon
    elif coords and isinstance(coords[0], list) and isinstance(coords[0][0], list):
        ring = coords[0]
        lons = [pt[0] for pt in ring]
        lats = [pt[1] for pt in ring]

    else:
        raise RuntimeError(f"grid2ll: unrecognized coordinates format: {coords}")

    min_lon = min(lons)
    max_lon = max(lons)
    min_lat = min(lats)
    max_lat = max(lats)

    return (min_lon, min_lat, max_lon, max_lat)


# in ThePython.py

def run_dnbr_job(fire_id, pre_start, pre_end, post_start, post_end, path, row, api_key):
    """
    Full pipeline for one fire or one custom request.
    Returns dict with file paths + stats + bounds.
    """
    pre_bands = download_landsat_period(api_key, pre_start, pre_end, path, row)
    post_bands = download_landsat_period(api_key, post_start, post_end, path, row)

    nbr_pre, nbr_post, delta, out_profile = process_landsat(
        pre_bands["nir"], pre_bands["swir"],
        post_bands["nir"], post_bands["swir"],
        pre_bands["qa"],  post_bands["qa"]
    )

    # ---- write GeoTIFF ----
    out_tif = os.path.join(OUTPUT_DIR, f"{fire_id}_delta_nbr.tif")
    profile = out_profile.copy()
    profile.update({
        "driver": "GTiff",
        "dtype": "float32",
        "count": 1,
        "nodata": -9999.0,
    })

    delta_to_write = np.where(
        np.isnan(delta),
        profile["nodata"],
        delta
    ).astype("float32")

    with rasterio.open(out_tif, "w", **profile) as dst:
        dst.write(delta_to_write, 1)

    # ---- write classified PNG using your USGS scale ----
    out_png = os.path.join(OUTPUT_DIR, f"{fire_id}_dnbr_usgs.png")
    export_dnbr_class_png(out_tif, out_png)   # the function we discussed earlier

    stats = delta_nbr_stats(delta)            # already returns % and can include area
    bounds = get_latlon_bounds(profile)

    return {
        "fire_id": fire_id,
        "pre_start": pre_start,
        "pre_end": pre_end,
        "post_start": post_start,
        "post_end": post_end,
        "path": path,
        "row": row,
        "tif_path": out_tif,
        "png_path": out_png,
        "stats": stats,
        "bounds": {
            "min_lat": bounds[0],
            "min_lon": bounds[1],
            "max_lat": bounds[2],
            "max_lon": bounds[3],
        },
    }

# --- keep all your functions above here: load_band, download_landsat_period, process_landsat, etc. ---

def run_delta_nbr_pipeline(
    api_key,
    pre_start, pre_end,
    post_start, post_end,
    path, row
):
    """
    Core function: given dates + WRS-2 path/row, run the whole pipeline
    and return useful info (paths, stats, bounds).
    This is what JS will indirectly trigger.
    """
    pre_bands = download_landsat_period(api_key, pre_start, pre_end, path, row)
    post_bands = download_landsat_period(api_key, post_start, post_end, path, row)

    nbr_pre, nbr_post, delta, out_profile = process_landsat(
        pre_bands["nir"], pre_bands["swir"],
        post_bands["nir"], post_bands["swir"],
        pre_bands["qa"],  post_bands["qa"]
    )

    out_tif = os.path.join(OUTPUT_DIR, "delta_nbr_float32_nd.tif")
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

    with rasterio.open(out_tif, "w", **out_profile) as dst:
        dst.write(delta_to_write, 1)

    out_png = os.path.join(OUTPUT_DIR, "delta_nbr_web.png")
    export_png_from_tif(out_tif, out_png)

    bounds = get_latlon_bounds(out_profile)

    # Maybe also return stats here
    stats = delta_nbr_stats(delta)

    return {
        "tif_path": out_tif,
        "png_path": out_png,
        "bounds": bounds,          # (min_lat, min_lon, max_lat, max_lon)
        "stats": stats
    }








def export_png_from_tif(tif_path, png_path):
    """
    Create a nicely-stretched PNG from a single-band GeoTIFF and
    write a PNG world file (.pgw) so it has georeferencing. had to make this long so the png didnt just show up as blank
    """
    with rasterio.open(tif_path) as src:
        data = src.read(1).astype("float32")
        transform = src.transform
        nodata = src.nodata

        # Mask nodata to NaN
        if nodata is not None:
            data = np.where(data == nodata, np.nan, data)

        valid = np.isfinite(data)

        if np.any(valid):
            # Use percentiles so the contrast looks good
            vmin = np.nanpercentile(data[valid], 2)
            vmax = np.nanpercentile(data[valid], 98)
            if vmin == vmax:
                vmin = np.nanmin(data[valid])
                vmax = np.nanmax(data[valid])
        else:
            # Fallback if everything is NaN
            vmin, vmax = 0.0, 1.0

        # Save PNG with a colormap and explicit scaling
        plt.imsave(png_path, data, cmap="inferno", vmin=vmin, vmax=vmax)

    # ----- Write a PNG world file (.pgw) for location -----
    # Pixel size (x,y)
    pixel_width = transform.a
    pixel_height = transform.e  # usually negative

    # Upper-left pixel *center* in the raster CRS
    x_ul, y_ul = xy(transform, 0, 0, offset="center")

    worldfile_path = os.path.splitext(png_path)[0] + ".pgw"
    with open(worldfile_path, "w") as f:
        f.write(f"{pixel_width}\n")  # pixel size in X
        f.write("0.0\n")             # rotation about Y (usually 0)
        f.write("0.0\n")             # rotation about X (usually 0)
        f.write(f"{pixel_height}\n") # pixel size in Y (negative for north-up)
        f.write(f"{x_ul}\n")         # X of center of upper-left pixel
        f.write(f"{y_ul}\n")         # Y of center of upper-left pixel

    print("Wrote PNG:", png_path)
    print("Wrote world file:", worldfile_path)



def m2m_logout(api_key):
    """
    Optional: log out to invalidate the API key.
    """
    url = SERVICE_URL + "logout"
    headers = {"X-Auth-Token": api_key}
    try:
        resp = requests.post(url, headers=headers, json=None)
        if resp.ok:
            print("Logged out of M2M.")
        else:
            print("Logout returned status:", resp.status_code)
    except Exception as e:
        print("Logout failed:", e)



from rasterio.transform import array_bounds
from pyproj import Transformer

def get_latlon_bounds(profile):
    """
    Compute lat/lon bounds (min_lat, min_lon, max_lat, max_lon)
    from a rasterio profile.
    """
    transform = profile["transform"]
    width, height = profile["width"], profile["height"]

    # bounds = (min_x, min_y, max_x, max_y) in the raster CRS
    bounds = array_bounds(height, width, transform)

    # Reproject corners to WGS84
    transformer = Transformer.from_crs(profile["crs"], "EPSG:4326", always_xy=True)
    lon_min, lat_min = transformer.transform(bounds[0], bounds[1])
    lon_max, lat_max = transformer.transform(bounds[2], bounds[3])

    return (lat_min, lon_min, lat_max, lon_max)






#------------------below i do my functions , most of them being inside a mega function: process landsat--------------------------------------------------

def process_landsat(pre_nir_path, pre_swir_path, post_nir_path, post_swir_path, qa_pre_path, qa_post_path):

    #these are the loadband and load cloud mask functions
    nir_pre, pre_profile = load_band(pre_nir_path)
    swir_pre, _ = load_band(pre_swir_path)
    mask_pre = load_cloud_mask(qa_pre_path)

    nir_post, post_profile = load_band(post_nir_path)
    swir_post, _ = load_band(post_swir_path)
    mask_post = load_cloud_mask(qa_post_path)


    #now for the combination of masks (but first i need to match them up using my align_raster function bc theyre not identical pixle locations)
    mask_post_aligned = align_mask(mask_post, post_profile, pre_profile)
    mask_both = mask_pre | mask_post_aligned
    #print("Mask Pre True count:", np.sum(mask_pre)) 
    #print("Mask Post True count:", np.sum(mask_post))
    #print("Mask Both True count:", np.sum(mask_both)) 
    #print("Mask Both total pixels:", mask_both.size)
    #print("Mask Both True %:", np.sum(mask_both) / mask_both.size * 100)

    #this is realigning postfire bands to prefire bands 
    nir_post_aligned = align_raster(nir_post, post_profile, pre_profile)
    swir_post_aligned = align_raster(swir_post, post_profile, pre_profile)
    #print("Pre NIR min/max:", np.nanmin(nir_pre), np.nanmax(nir_pre))
    #print("Pre SWIR min/max:", np.nanmin(swir_pre), np.nanmax(swir_pre))
    #print("Post NIR (aligned) min/max:", np.nanmin(nir_post_aligned), np.nanmax(nir_post_aligned))
    #print("Post SWIR (aligned) min/max:", np.nanmin(swir_post_aligned), np.nanmax(swir_post_aligned))

    
    #compute nbr
    nbr_pre = compute_nbr(nir_pre, swir_pre, mask_both)
    nbr_post = compute_nbr(nir_post_aligned, swir_post_aligned, mask_both)

    #delta nbr
    delta = compute_delta_nbr(nbr_pre, nbr_post)

    #compute stats
    stats = delta_nbr_stats(delta)
    print(stats)
    return nbr_pre, nbr_post, delta, pre_profile




#-----------------------------------------------------------------------------------
os.makedirs(OUTPUT_DIR, exist_ok=True)


if __name__ == "__main__":
    username = os.environ.get("USGS_USERNAME")
    app_token = os.environ.get("USGS_TOKEN")

    if not username or not app_token:
        raise RuntimeError("USGS_USERNAME / USGS_TOKEN not set in environment.")

    api_key = m2m_login(username, app_token)

    pre_start = input("Enter pre-fire start date (YYYY-MM-DD): ")
    pre_end   = input("Enter pre-fire end date (YYYY-MM-DD): ")
    post_start = input("Enter post-fire start date (YYYY-MM-DD): ")
    post_end   = input("Enter post-fire end date (YYYY-MM-DD): ")

    path, row = map(int, input("Enter WRS-2 path,row (e.g., 17,23): ").split(","))

    # ↓↓↓ NOW this only needs path,row + dates ↓↓↓
    pre_bands = download_landsat_period(api_key, pre_start, pre_end, path, row)
    post_bands = download_landsat_period(api_key, post_start, post_end, path, row)

    nbr_pre, nbr_post, delta, out_profile = process_landsat(
        pre_bands["nir"], pre_bands["swir"],
        post_bands["nir"], post_bands["swir"],
        pre_bands["qa"],  post_bands["qa"]
    )

    out_tif = os.path.join(OUTPUT_DIR, "delta_nbr_float32_nd.tif")
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

    with rasterio.open(out_tif, "w", **out_profile) as dst:
        dst.write(delta_to_write, 1)

    print("Wrote:", out_tif)

    out_png = os.path.join(OUTPUT_DIR, "delta_nbr_usgs_classes.png")
    export_dnbr_class_png(out_tif, out_png)

    print("PNG ready for web:", out_png)

    print("Lat/lon bounds:", get_latlon_bounds(out_profile))

    m2m_logout(api_key)
