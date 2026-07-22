from pathlib import Path

from flask import Flask, jsonify, request

from backend.data import debris_from_record, generate_baseline_trajectory, get_debris, get_debris_payload, xyz_to_lat_lng_alt
from backend.evaluation import compute_metrics
from backend.model_inference import ModelService

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"
MODEL_DIR = BASE_DIR / "model.keras"
if not MODEL_DIR.exists():
    MODEL_DIR = BASE_DIR / "best_lstm_model.keras"

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
model_service = ModelService(MODEL_DIR)


@app.get("/")
def index() -> str:
    return app.send_static_file("index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/debris")
def debris_catalog() -> object:
    return jsonify({"items": get_debris_payload()})


@app.get("/api/model/status")
def model_status() -> object:
    return jsonify(model_service.status)


@app.route("/api/trajectory", methods=["GET", "POST"])
def trajectory() -> object:
    payload = request.get_json(silent=True) or {}
    horizon_mins = int(payload.get("horizon_mins") or request.args.get("horizon_mins", "180"))
    horizon_mins = max(30, min(720, horizon_mins))

    if request.method == "POST" and payload:
        debris = debris_from_record(payload.get("debris", payload))
    else:
        debris_id = request.args.get("debris_id", "NORAD-25544")
        debris = get_debris(debris_id)

    rows = generate_baseline_trajectory(debris, horizon_mins)

    for row in rows:
        raw = row["raw"]
        dx_model, dy_model, dz_model = model_service.predict_delta(
            [
                raw["x"],
                raw["y"],
                raw["z"],
                raw["vx"],
                raw["vy"],
                raw["vz"],
                raw["altKm"],
                debris.bstar,
            ]
        )

        corrected_x = raw["x"] + dx_model
        corrected_y = raw["y"] + dy_model
        corrected_z = raw["z"] + dz_model
        corrected_lat, corrected_lng, corrected_alt = xyz_to_lat_lng_alt(
            corrected_x, corrected_y, corrected_z
        )

        row["corrected"] = {
            "lat": corrected_lat,
            "lng": corrected_lng,
            "altKm": corrected_alt,
            "x": corrected_x,
            "y": corrected_y,
            "z": corrected_z,
        }
        row["modelDelta"] = {"dx": dx_model, "dy": dy_model, "dz": dz_model}

    metrics = compute_metrics(rows)

    return jsonify(
        {
            "debris": {
                "id": debris.object_id,
                "name": debris.name,
                "tle": [debris.tle1, debris.tle2],
            },
            "rows": rows,
            "metrics": metrics,
            "modelStatus": model_service.status,
            "meta": {
                "featureOrder": [
                    "x",
                    "y",
                    "z",
                    "vx",
                    "vy",
                    "vz",
                    "altitude",
                    "bstar",
                ],
                "outputOrder": ["dx", "dy", "dz"],
                "stepMins": 3,
            },
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
