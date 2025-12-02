# Burn viewer MVP

Test commit from new Mac

## XYZ tiles (faster than preloaded PNG overlays)

1) Make sure `gdal2tiles.py` is on your PATH (comes with GDAL 3.x).
2) Generate tile pyramids + manifest from the batch outputs:
   ```
   # If you want the one-shot helper:
   python srcPYTHON/make_xyz_tiles.py --zoom 6-12
   ```
   - Reads outputs from `data/outputs/batch_tiles/` (now includes *_rgba.tif).
   - Writes XYZ tiles under `assets/xyz/<tile-id>/{z}/{x}/{y}.png`.
   - Emits `assets/xyz/tiles_manifest.json` with tileUrl/minZoom/maxZoom.
   Or run the lightweight wrapper for a single RGBA GeoTIFF:
   ```
   python srcPYTHON/gdal2tiles_runner.py --input <your_rgba.tif> --zoom 6-12 --srcnodata 0 0 0 0
   ```
3) Rebuild the preset snippet so the UI can use the XYZ tiles:
   ```
   python srcPYTHON/list_titles_for_frontent.py > tiles_snippet.js
   ```
   (the script will include `tileUrl` automatically if the manifest exists).
4) The Leaflet map now prefers `tileUrl` when present; it falls back to the
   original PNG overlays, so you can mix both during the transition.

Note: The pipelines now also emit an RGBA GeoTIFF alongside the float dNBR and PNG
(`*_rgba.tif`); use that as the source for gdal2tiles to preserve colours/alpha.
