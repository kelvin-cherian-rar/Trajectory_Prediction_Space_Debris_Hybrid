"""
Create fallback scalers based on typical orbital debris ranges.
Run this if scaler_X.pkl and scaler_y.pkl are missing.
"""

import joblib
from pathlib import Path
from sklearn.preprocessing import StandardScaler
import numpy as np


def create_fallback_scalers():
    """
    Generate scalers based on typical Earth orbital debris characteristics.
    Used as fallback when trained scalers are unavailable.
    """
    
    # Typical ranges for LEO debris (Low Earth Orbit)
    # These are approximate means and stds based on orbital mechanics
    
    # Feature: [x, y, z, vx, vy, vz, altitude, bstar]
    # All positions in km, velocities in km/s, altitude in km, bstar in 1/RE
    
    feature_means = np.array([
        -5500.0,      # x (km) - Earth radius ~6371
        2500.0,       # y (km)
        2500.0,       # z (km)
        0.0,          # vx (km/s) - velocity relative to Earth
        7.0,          # vy (km/s) - typical orbital velocity
        3.0,          # vz (km/s)
        500.0,        # altitude (km) - typical LEO altitude
        -3.0e-4,      # bstar - drag coefficient exponent
    ])
    
    feature_stds = np.array([
        2000.0,       # x std
        3000.0,       # y std
        3000.0,       # z std
        0.5,          # vx std
        2.0,          # vy std
        2.0,          # vz std
        150.0,        # altitude std
        2.0e-4,       # bstar std
    ])
    
    # Target: [dx, dy, dz] - change per timestep
    target_means = np.array([
        0.0,          # dx - zero mean (no preferential direction)
        0.0,          # dy
        0.0,          # dz
    ])
    
    target_stds = np.array([
        10.0,         # dx std (km per minute)
        10.0,         # dy std
        10.0,         # dz std
    ])
    
    # Create scalers
    scaler_X = StandardScaler()
    scaler_X.mean_ = feature_means
    scaler_X.scale_ = feature_stds
    scaler_X.var_ = feature_stds ** 2
    scaler_X.n_features_in_ = 8
    
    scaler_y = StandardScaler()
    scaler_y.mean_ = target_means
    scaler_y.scale_ = target_stds
    scaler_y.var_ = target_stds ** 2
    scaler_y.n_features_in_ = 3
    
    return scaler_X, scaler_y


def save_fallback_scalers(model_dir: Path = None):
    """Save fallback scalers to model directory."""
    if model_dir is None:
        # Try model.keras first, fall back to best_lstm_model.keras
        base_dir = Path(__file__).parent
        if (base_dir / "model.keras").exists():
            model_dir = base_dir / "model.keras"
        else:
            model_dir = base_dir / "best_lstm_model.keras"
    
    model_dir = Path(model_dir)
    
    # If it's a .keras file, save scalers next to it
    if model_dir.is_file() and model_dir.suffix == ".keras":
        scaler_dir = model_dir.parent
    else:
        scaler_dir = model_dir
    
    scaler_dir.mkdir(parents=True, exist_ok=True)
    
    scaler_X, scaler_y = create_fallback_scalers()
    
    # Save
    joblib.dump(scaler_X, scaler_dir / "scaler_X.pkl")
    joblib.dump(scaler_y, scaler_dir / "scaler_y.pkl")
    
    print(f"✓ Fallback scalers saved to {model_dir}")
    print(f"  scaler_X: mean={scaler_X.mean_}, std={scaler_X.scale_}")
    print(f"  scaler_y: mean={scaler_y.mean_}, std={scaler_y.scale_}")
    print("\n⚠ Note: These are estimates based on typical orbital ranges.")
    print("  For best accuracy, export scalers from your training notebook!")


if __name__ == "__main__":
    save_fallback_scalers()
