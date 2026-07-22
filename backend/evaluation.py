import math


def xyz_error_km(a: dict[str, float], b: dict[str, float]) -> float:
    dx = a["x"] - b["x"]
    dy = a["y"] - b["y"]
    dz = a["z"] - b["z"]
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def compute_metrics(rows: list[dict[str, object]]) -> dict[str, object]:
    raw_errors = []
    corrected_errors = []

    for row in rows:
        raw_errors.append(xyz_error_km(row["raw"], row["observed"]))
        corrected_errors.append(xyz_error_km(row["corrected"], row["observed"]))

    rmse_raw = math.sqrt(sum(v * v for v in raw_errors) / len(raw_errors))
    rmse_corrected = math.sqrt(sum(v * v for v in corrected_errors) / len(corrected_errors))
    mae_raw = sum(abs(v) for v in raw_errors) / len(raw_errors)
    mae_corrected = sum(abs(v) for v in corrected_errors) / len(corrected_errors)

    return {
        "rawErrors": raw_errors,
        "correctedErrors": corrected_errors,
        "rmseRaw": rmse_raw,
        "rmseCorrected": rmse_corrected,
        "maeRaw": mae_raw,
        "maeCorrected": mae_corrected,
    }
