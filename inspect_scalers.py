from backend.model_inference import ModelService
from pathlib import Path
m=ModelService(Path('best_lstm_model.keras'))
print('Status warnings:', m.status.get('warnings', []))
if m.scaler_x is not None:
    try:
        print('scaler_X mean:', m.scaler_x.mean_)
        print('scaler_X scale:', m.scaler_x.scale_)
    except Exception as e:
        print('Error reading scaler_X:', e)
if m.scaler_y is not None:
    try:
        print('scaler_y mean:', m.scaler_y.mean_)
        print('scaler_y scale:', m.scaler_y.scale_)
    except Exception as e:
        print('Error reading scaler_y:', e)
