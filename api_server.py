import sys
import os
from flask import Flask, request, jsonify, send_from_directory

# --- make sure we can import ThePython.py from srcPYTHON/ ---

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "srcPYTHON")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from ThePython import (
    run_delta_nbr_pipeline,
    m2m_login,
    m2m_logout,
    OUTPUT_DIR,
)

app = Flask(
    __name__,
    static_folder="webmap",      # where index.html, map.html, css/js live
    static_url_path=""           # so /map.html, /css/styles.css work
)

# --- serve the existing frontend ---

@app.route("/")
def root():
    # this will serve webmap/index.html
    return app.send_static_file("index.html")

# map.html, css, js will be served automatically from static_folder
# e.g. /map.html -> webmap/map.html, /js/map.js -> webmap/js/map.js


# --- API endpoint: run delta NBR for a given path/row + dates ---

@app.route("/api/run_dnbr", methods=["POST"])
def api_run_dnbr():
    data = request.get_json(force=True) or {}

    # Basic validation / parsing
    try:
        path = int(data["path"])
        row = int(data["row"])
        pre_start  = data["pre_start"]
        pre_end    = data["pre_end"]
        post_start = data["post_start"]
        post_end   = data["post_end"]
    except (KeyError, ValueError) as e:
        return jsonify({"error": f"Missing or invalid parameter: {e}"}), 400

    username = os.environ.get("USGS_USERNAME")
    token    = os.environ.get("USGS_TOKEN")
    if not username or not token:
        return jsonify({"error": "USGS_USERNAME / USGS_TOKEN not set"}), 500

    api_key = m2m_login(username, token)

    try:
        # This is your existing function from ThePython.py
        result = run_delta_nbr_pipeline(
            api_key,
            pre_start, pre_end,
            post_start, post_end,
            path, row
        )
    except Exception as e:
        # bubble up error to frontend
        return jsonify({"error": str(e)}), 500
    finally:
        m2m_logout(api_key)

    # result should have: "tif_path", "png_path", "bounds", "stats"
    png_path = result.get("png_path")
    bounds   = result.get("bounds")
    stats    = result.get("stats")

    # Make a filename relative to OUTPUT_DIR, so we can serve it later if we want
    png_url = None
    if png_path and png_path.startswith(OUTPUT_DIR):
        rel_name = os.path.basename(png_path)
        png_url = f"/outputs/{rel_name}"

    return jsonify({
        "stats": stats,
        "bounds": {
            "min_lat": bounds[0],
            "min_lon": bounds[1],
            "max_lat": bounds[2],
            "max_lon": bounds[3],
        } if bounds else None,
        "png_url": png_url
    })


# (optional) serve generated PNGs from OUTPUT_DIR
@app.route("/outputs/<path:filename>")
def serve_output_file(filename):
    return send_from_directory(OUTPUT_DIR, filename)


if __name__ == "__main__":
    # Make sure Flask is installed: pip install flask
    app.run(host="127.0.0.1", port=5000, debug=True)
