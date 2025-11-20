import rasterio
import numpy as np

p = 'outputs/delta_nbr.tif'
with rasterio.open(p) as src:
    print("path:", p)
    print("driver:", src.driver)
    print("width,height:", src.width, src.height)
    print("count:", src.count)
    print("crs:", src.crs)
    print("dtype:", src.dtypes)
    print("nodata:", src.nodatavals)
    arr = src.read(1, masked=True)   # masked array honors nodata
    print("masked array dtype:", arr.dtype)
    print("mask (all masked?):", arr.mask.all())
    try:
        # statistics ignoring mask
        print("min/max (raw):", np.nanmin(arr.data), np.nanmax(arr.data))
        print("non-masked count:", np.count_nonzero(~arr.mask))
    except Exception as e:
        print("stat error:", e)
