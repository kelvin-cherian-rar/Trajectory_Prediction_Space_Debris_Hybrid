# Space Debris Trajectory Detection

A Flask-backed orbit visualization and trajectory correction demo for orbital debris. This project combines a synthetic debris catalog, a TensorFlow LSTM correction model, and a browser-based globe UI to compare raw baseline trajectories, ML-corrected trajectories, and observed ground-truth paths.

## What this project does

- Serves a single-page web app from `app.py` using Flask.
- Loads debris catalog entries from `data/debris_catalog.csv` (or built-in fallback catalog).
- Generates a baseline debris trajectory and applies learned corrections from a saved TensorFlow model.
- Computes evaluation metrics and returns raw/corrected/observed trajectories via a JSON API.
- Displays results on a 3D globe with error plots in the browser.

## Why it is useful

- Demonstrates how machine learning can improve orbit prediction for space debris monitoring.
- Provides an end-to-end prototype with backend inference, model diagnostics, and frontend visualization.
- Useful for rapid experimentation with TLE-based debris propagation, model correction, and trajectory error analysis.

## Key features

- Flask REST API for debris catalog, model status, and trajectory prediction
- Synthetic baseline trajectory generation in `backend/data.py`
- LSTM model inference with `backend/model_inference.py`
- Error metrics RMSE/MAE computed by `backend/evaluation.py`
- Browser globe visualization and charts in `frontend/`

## Prerequisites

- Python 3.11+ recommended
- `pip` available
- `requirements.txt` dependencies:
  - Flask
  - NumPy
  - TensorFlow
  - joblib

## Installation

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> If you use PowerShell and execution policy blocks activation, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` first.

## Running the app

From the root directory:

```powershell
python app.py
```

Open the app in your browser:

- `http://localhost:5000`

Health check:

- `http://localhost:5000/health`

Model status:

- `http://localhost:5000/api/model/status`

## API endpoints

- `GET /api/debris` — returns debris catalog items for the frontend.
- `GET /api/model/status` — returns model/scaler status and warnings.
- `GET /api/trajectory` — returns trajectory rows for a default or selected debris object.
- `POST /api/trajectory` — accepts JSON payload with debris/TLE data and optional `horizon_mins`, then returns raw/corrected/observed trajectory rows.

### Example POST payload

```json
{
  "debris": {
    "id": "NORAD-25544",
    "name": "ISS Fragment Cluster A",
    "tle1": "1 25544U 98067A   26096.51234567  .00007852  00000-0  14421-3 0  9997",
    "tle2": "2 25544  51.6438 250.1219 0005380  67.2032  22.4421 15.49812376490122",
    "bstar": 0.00014421
  },
  "horizon_mins": 180
}
```

## Model and assets

- The app prefers `model.keras` if present, otherwise uses `best_lstm_model.keras`.
- Scalar artifacts are expected in the same directory as the `.keras` model:
  - `scaler_X.pkl`
  - `scaler_y.pkl`
- If scalers are missing, the app still runs but may return unscaled predicted deltas and model warnings.

## Project structure

- `app.py` — Flask application entry point
- `backend/` — core data generation, evaluation, and model inference logic
- `frontend/` — static web UI assets and globe visualization
- `data/` — debris catalog and observational data
- `requirements.txt` — Python dependencies
- `best_lstm_model.keras` — default saved model artifact
- `model_training.ipynb` — notebook for training or inspecting model behavior

## Notes

- The current trajectory generator in `backend/data.py` is a synthetic baseline implementation. It is designed to be replaced with a proper SGP4 or orbital dynamics pipeline if desired.
- The frontend already supports live TLE catalog retrieval from CelesTrak and can POST selected TLE data to `/api/trajectory`.

## Related documentation

- `frontend/README.md` — frontend-specific setup and usage details
- `data/README.md` — data file and observation notes

## Contributing

1. Fork the repository.
2. Create a feature branch.
3. Submit a pull request with a clear description of changes.

If you want to add a full `CONTRIBUTING.md`, link it from this README later.
