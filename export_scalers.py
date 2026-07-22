"""
Quick script to export scalers from the training notebook.
Add this cell to your model_training.ipynb after model training is complete:

import joblib
import pandas as pd
from sklearn.preprocessing import StandardScaler

# Reload the training data
df = pd.read_csv("error_dataset.csv")

# Recreate scalers (fit on training data same way as in notebook)
X = df[["x","y","z","vx","vy","vz","altitude","bstar"]]
y = df[["dx","dy","dz"]]

scaler_X = StandardScaler()
scaler_X.fit(X)

scaler_y = StandardScaler()
scaler_y.fit(y)

# Export to model directory
joblib.dump(scaler_X, 'best_lstm_model.keras/scaler_X.pkl')
joblib.dump(scaler_y, 'best_lstm_model.keras/scaler_y.pkl')

print("✓ Scalers exported successfully!")
print(f"  X features: {X.shape[1]}, y targets: {y.shape[1]}")
print(f"  X means: {scaler_X.mean_}")
print(f"  y means: {scaler_y.mean_}")
"""

print(__doc__)

# If run directly, help extract scalers
import sys
from pathlib import Path

notebook_path = Path("model_training.ipynb")
if notebook_path.exists():
    print("\n✓ Found model_training.ipynb")
    print("\nTo fix the model accuracy:")
    print("1. Open model_training.ipynb")
    print("2. After the model.save() cell, run the SCALER EXPORT cell (already added)")
    print("3. This will save scaler_X.pkl and scaler_y.pkl")
    print("4. The backend will automatically load them on next startup")
else:
    print("\n✗ model_training.ipynb not found")
    print("Please ensure you're in the spaceDebris directory")
