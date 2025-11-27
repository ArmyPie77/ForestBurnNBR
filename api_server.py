import os
import sys
from flask import Flask, request, jsonify, send_from_directory

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

app = Flask(__name__, static_folder=".", static_url_path="")


@app.route("/")
def root():
    return app.send_static_file("index.html")


def _validate_iso_date(label, value):
    import re
    if not isinstance(value, str) or not re.match(r"^\d{4}-\d{2}-\d{2}$", value):
        raise ValueError(f"{label} must be YYYY-MM-DD")


@app.route("/api/run_dnbr", methods=["POST"])
def api_run_dnbr():
    data = request.get_json(force=True) or {}
    try:
        path = int(data["path"])
        row = int(data["row"])
        pre_start = data["pre_start"]
        pre_end = data["pre_end"]
        post_start = data["post_start"]
        post_end = data["post_end"]
        _validate_iso_date("pre_start", pre_start)
        _validate_iso_date("pre_end", pre_end)
        _validate_iso_date("post_start", post_start)
        _validate_iso_date("post_end", post_end)
    except (KeyError, ValueError) as e:
        return jsonify({"error": f"Missing or invalid parameter: {e}"}), 400

    username = os.environ.get("USGS_USERNAME")
    token = os.environ.get("USGS_TOKEN")
    if not username or not token:
        return jsonify({"error": "USGS_USERNAME / USGS_TOKEN not set"}), 500

    api_key = m2m_login(username, token)
    tag = f"p{path:03d}r{row:03d}_{pre_start.replace('-', '')}_{post_start.replace('-', '')}"

    try:
        result = run_delta_nbr_pipeline(
            api_key,
            pre_start,
            pre_end,
            post_start,
            post_end,
            path,
            row,
            tag=tag,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        m2m_logout(api_key)

    png_path = result.get("png_path")
    bounds = result.get("bounds")
    stats = result.get("stats")
    png_url = None
    if png_path and png_path.startswith(OUTPUT_DIR):
        png_url = f"/outputs/{os.path.basename(png_path)}"

    return jsonify(
        {
            "stats": stats,
            "bounds": {
                "min_lat": bounds[0],
                "min_lon": bounds[1],
                "max_lat": bounds[2],
                "max_lon": bounds[3],
            }
            if bounds
            else None,
            "png_url": png_url,
        }
    )


@app.route("/api/run_dnbr_batch", methods=["POST"])
def api_run_dnbr_batch():
    data = request.get_json(force=True) or {}
    reqs = data.get("requests")
    if not isinstance(reqs, list) or not reqs:
        return jsonify({"error": "requests must be a non-empty list"}), 400

    try:
        first = reqs[0]
        pre_start = first["pre_start"]
        pre_end = first["pre_end"]
        post_start = first["post_start"]
        post_end = first["post_end"]
        _validate_iso_date("pre_start", pre_start)
        _validate_iso_date("pre_end", pre_end)
        _validate_iso_date("post_start", post_start)
        _validate_iso_date("post_end", post_end)
    except (KeyError, ValueError) as e:
        return jsonify({"error": f"Missing or invalid parameter: {e}"}), 400

    username = os.environ.get("USGS_USERNAME")
    token = os.environ.get("USGS_TOKEN")
    if not username or not token:
        return jsonify({"error": "USGS_USERNAME / USGS_TOKEN not set"}), 500

    api_key = m2m_login(username, token)
    results = []
    errors = []
    try:
        for idx, r in enumerate(reqs):
            try:
                path = int(r["path"])
                row = int(r["row"])
            except (KeyError, ValueError) as e:
                errors.append({"index": idx, "error": f"Missing or invalid path/row: {e}"})
                continue

            tag = f"p{path:03d}r{row:03d}_{pre_start.replace('-', '')}_{post_start.replace('-', '')}"
            try:
                res = run_delta_nbr_pipeline(
                    api_key,
                    pre_start,
                    pre_end,
                    post_start,
                    post_end,
                    path,
                    row,
                    tag=tag,
                )
            except Exception as e:
                errors.append({"path": path, "row": row, "error": str(e)})
                continue

            png_path = res.get("png_path")
            bounds = res.get("bounds")
            stats = res.get("stats")
            png_url = None
            if png_path and png_path.startswith(OUTPUT_DIR):
                png_url = f"/outputs/{os.path.basename(png_path)}"

            results.append(
                {
                    "path": path,
                    "row": row,
                    "stats": stats,
                    "bounds": {
                        "min_lat": bounds[0],
                        "min_lon": bounds[1],
                        "max_lat": bounds[2],
                        "max_lon": bounds[3],
                    }
                    if bounds
                    else None,
                    "png_url": png_url,
                }
            )
    finally:
        m2m_logout(api_key)

    return jsonify({"results": results, "errors": errors})


@app.route("/outputs/<path:filename>")
def serve_output_file(filename):
    return send_from_directory(OUTPUT_DIR, filename)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
