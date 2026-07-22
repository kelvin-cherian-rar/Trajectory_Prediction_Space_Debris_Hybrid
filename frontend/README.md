# Space Debris Frontend (Globe View)

This frontend visualizes orbital debris trajectories with three layers:

- Raw SGP4 trajectory (baseline)
- ML-corrected trajectory
- Observed/ground-truth trajectory

It also shows RMSE/MAE and an error-over-time chart.

The UI now pulls live TLE data directly from CelesTrak in the browser and sends the selected TLE pair to Flask for prediction.

- CelesTrak feed: `cosmos-2251-debris`
- `/api/trajectory` accepts POSTed TLE/object data and returns raw, corrected, and observed trajectories + metrics

## Run With Flask

From the project root, create/activate your Python environment, install dependencies, and start Flask:

```powershell
pip install -r requirements.txt
python app.py
```

Then open:

- http://localhost:5000

Optional health check:

- http://localhost:5000/health

Model diagnostics:

- http://localhost:5000/api/model/status

## Hooking to your real pipeline

To match training-time inference exactly, place scaler artifacts inside `model.keras/`:

- `scaler_X.pkl`
- `scaler_y.pkl`

Without these scalers, inference still runs but the API will report warnings and corrections may be mis-scaled.

Feature order expected by the model:

1. x
2. y
3. z
4. vx
5. vy
6. vz
7. altitude
8. bstar

Model output order:

1. dx
2. dy
3. dz

If you want to replace the synthetic baseline generator with true SGP4 propagation, update backend data generation logic in `backend/data.py`.

1. Replace `debrisCatalog` with objects from your TLE + metadata source.
2. Replace `generateTrajectory()` so it consumes:
   - SGP4 outputs (x, y, z) from backend
   - ML correction outputs (dx, dy, dz)
   - Observed positions for evaluation
3. Keep `evaluateTrajectory()` and rendering functions as-is, or route metrics from backend.

If your backend returns ECI or ECEF Cartesian coordinates, convert to lat/lng/alt before passing to globe paths.
