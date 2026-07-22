import json
import tempfile
import zipfile
from pathlib import Path

import numpy as np

try:
    import joblib
except ImportError:  # pragma: no cover
    joblib = None

try:
    from tensorflow import keras
except Exception:  # pragma: no cover
    keras = None


class ModelService:
    def __init__(self, model_dir: Path):
        self.model_dir = model_dir
        self.model = None
        self.scaler_x = None
        self.scaler_y = None
        self.status = {
            "modelLoaded": False,
            "scalerXLoaded": False,
            "scalerYLoaded": False,
            "warnings": [],
            "modelInputShape": None,
            "modelOutputShape": None,
        }

        self._load_assets()

    def _load_assets(self) -> None:
        if keras is None:
            self.status["warnings"].append("TensorFlow is not installed. Returning baseline-only corrections.")
            return

        model_path = self.model_dir
        if not model_path.exists():
            self.status["warnings"].append(f"Model path not found: {model_path}")
            return

        self.model = self._load_keras_model(model_path)
        if self.model is None:
            self.status["warnings"].append("Model could not be loaded. Serving baseline-only trajectory.")
            return

        self.status["modelLoaded"] = True
        self.status["modelInputShape"] = tuple(self.model.input_shape)
        self.status["modelOutputShape"] = tuple(self.model.output_shape)

        if joblib is None:
            self.status["warnings"].append("joblib is not installed, scalers cannot be loaded.")
            return

        # Handle both directory and file formats for model storage
        # If model_dir is a .keras file, look for scalers in parent directory
        if self.model_dir.is_file() and self.model_dir.suffix == ".keras":
            scaler_dir = self.model_dir.parent
        else:
            scaler_dir = self.model_dir

        scaler_x_path = scaler_dir / "scaler_X.pkl"
        scaler_y_path = scaler_dir / "scaler_y.pkl"

        if scaler_x_path.exists():
            try:
                self.scaler_x = joblib.load(scaler_x_path)
                self.status["scalerXLoaded"] = True
            except Exception as exc:  # pragma: no cover
                self.status["warnings"].append(f"scaler_X.pkl could not be loaded: {exc}")
        else:
            self.status["warnings"].append("scaler_X.pkl not found; using unscaled features.")

        if scaler_y_path.exists():
            try:
                self.scaler_y = joblib.load(scaler_y_path)
                self.status["scalerYLoaded"] = True
            except Exception as exc:  # pragma: no cover
                self.status["warnings"].append(f"scaler_y.pkl could not be loaded: {exc}")
        else:
            self.status["warnings"].append("scaler_y.pkl not found; using raw model outputs as dx/dy/dz.")

        metadata_path = scaler_dir / "metadata.json"
        if metadata_path.exists():
            try:
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                self.status["kerasVersion"] = metadata.get("keras_version")
            except json.JSONDecodeError:
                self.status["warnings"].append("metadata.json could not be parsed.")

    def _load_keras_model(self, model_path: Path):
        try:
            # Works for single-file .keras artifacts.
            return keras.models.load_model(model_path)
        except (PermissionError, IsADirectoryError, OSError, ValueError, TypeError) as exc:
            if model_path.is_file() and model_path.suffix == ".keras":
                model = self._load_from_keras_zip(model_path)
                if model is not None:
                    self.status["warnings"].append(
                        "Loaded model from .keras zip via compatibility path."
                    )
                    return model

            if not model_path.is_dir():
                self.status["warnings"].append(f"load_model failed: {exc}")
                return None

            config_path = model_path / "config.json"
            weights_path = model_path / "model.weights.h5"

            if not config_path.exists() or not weights_path.exists():
                self.status["warnings"].append(
                    "Directory model format missing config.json or model.weights.h5."
                )
                return None

            try:
                config = json.loads(config_path.read_text(encoding="utf-8"))
                cleaned_config = self._clean_config(config)

                model = keras.models.model_from_json(json.dumps(cleaned_config))
                model.load_weights(weights_path)
                self.status["warnings"].append(
                    "Loaded model from directory format (config.json + model.weights.h5)."
                )
                return model
            except Exception as dir_exc:  # pragma: no cover
                self.status["warnings"].append(f"Directory model load failed: {dir_exc}")
                return None

    def _load_from_keras_zip(self, keras_path: Path):
        try:
            with zipfile.ZipFile(keras_path, "r") as archive:
                config = json.loads(archive.read("config.json").decode("utf-8"))
                cleaned_config = self._clean_config(config)
                model = keras.models.model_from_json(json.dumps(cleaned_config))

                with tempfile.TemporaryDirectory() as temp_dir:
                    weights_path = Path(temp_dir) / "model.weights.h5"
                    with open(weights_path, "wb") as weights_file:
                        weights_file.write(archive.read("model.weights.h5"))
                    model.load_weights(weights_path)

                return model
        except Exception as zip_exc:  # pragma: no cover
            self.status["warnings"].append(f".keras compatibility load failed: {zip_exc}")
            return None

    def _clean_config(self, value):
        if isinstance(value, dict):
            cleaned = {}
            for key, item in value.items():
                # Saved-model metadata keys that break older runtime deserializers.
                if key in {"quantization_config", "shared_object_id"}:
                    continue
                cleaned[key] = self._clean_config(item)
            return cleaned

        if isinstance(value, list):
            return [self._clean_config(item) for item in value]

        return value

    def predict_delta(self, feature_vector: list[float]) -> tuple[float, float, float]:
        if not self.model:
            return 0.0, 0.0, 0.0

        x = np.array(feature_vector, dtype=np.float32).reshape(1, -1)

        if self.scaler_x is not None:
            x = self.scaler_x.transform(x)

        x_seq = x.reshape(1, 1, x.shape[1])
        y_pred = self.model.predict(x_seq, verbose=0)

        if self.scaler_y is not None:
            y_pred = self.scaler_y.inverse_transform(y_pred)

        delta = y_pred[0]
        return float(delta[0]), float(delta[1]), float(delta[2])
