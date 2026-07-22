import csv
import math
from dataclasses import dataclass
from pathlib import Path

EARTH_RADIUS_KM = 6371.0
STEP_MINS = 3
BASE_DIR = Path(__file__).resolve().parent.parent
CATALOG_PATH = BASE_DIR / "data" / "debris_catalog.csv"


@dataclass(frozen=True)
class DebrisObject:
    object_id: str
    name: str
    tle1: str
    tle2: str
    inclination_deg: float
    eccentricity: float
    mean_motion: float
    arg_perigee: float
    raan: float
    bstar: float
    seed: float


FALLBACK_DEBRIS_CATALOG = [
    DebrisObject(
        object_id="NORAD-25544",
        name="ISS Fragment Cluster A",
        tle1="1 25544U 98067A   26096.51234567  .00007852  00000-0  14421-3 0  9997",
        tle2="2 25544  51.6438 250.1219 0005380  67.2032  22.4421 15.49812376490122",
        inclination_deg=51.64,
        eccentricity=0.000538,
        mean_motion=15.49,
        arg_perigee=67.2,
        raan=250.1,
        bstar=1.4421e-4,
        seed=1.2,
    ),
    DebrisObject(
        object_id="NORAD-33591",
        name="Cosmos Debris C",
        tle1="1 33591U 09005A   26096.23985186  .00000247  00000-0  12673-3 0  9993",
        tle2="2 33591  98.7742 122.9940 0020731 256.3296 103.5564 14.24024577894356",
        inclination_deg=98.77,
        eccentricity=0.002073,
        mean_motion=14.24,
        arg_perigee=256.3,
        raan=122.9,
        bstar=1.2673e-4,
        seed=2.6,
    ),
    DebrisObject(
        object_id="NORAD-43013",
        name="Fengyun Fragment K",
        tle1="1 43013U 17073AF  26095.90223152  .00001132  00000-0  78544-4 0  9992",
        tle2="2 43013  97.3495  51.1238 0013017 221.6071 138.3782 15.22461925398195",
        inclination_deg=97.34,
        eccentricity=0.001302,
        mean_motion=15.22,
        arg_perigee=221.6,
        raan=51.1,
        bstar=7.8544e-5,
        seed=4.1,
    ),
]


def _to_float(value: str | float | int | None, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return default
    return float(text)


def _load_catalog_from_csv(path: Path) -> list[DebrisObject]:
    items: list[DebrisObject] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            items.append(
                DebrisObject(
                    object_id=row["id"].strip(),
                    name=row["name"].strip(),
                    tle1=row["tle1"].strip(),
                    tle2=row["tle2"].strip(),
                    inclination_deg=_to_float(row.get("inclination_deg")),
                    eccentricity=_to_float(row.get("eccentricity")),
                    mean_motion=_to_float(row.get("mean_motion")),
                    arg_perigee=_to_float(row.get("arg_perigee")),
                    raan=_to_float(row.get("raan")),
                    bstar=_to_float(row.get("bstar")),
                    seed=_to_float(row.get("seed"), 1.0),
                )
            )
    return items


def load_debris_catalog() -> list[DebrisObject]:
    if CATALOG_PATH.exists():
        return _load_catalog_from_csv(CATALOG_PATH)
    return FALLBACK_DEBRIS_CATALOG


def debris_from_record(record: dict[str, object]) -> DebrisObject:
    tle = record.get("tle") or []
    tle1 = record.get("tle1") or (tle[0] if len(tle) > 0 else "")
    tle2 = record.get("tle2") or (tle[1] if len(tle) > 1 else "")

    object_id = str(record.get("id") or record.get("object_id") or "")
    name = str(record.get("name") or object_id)

    return DebrisObject(
        object_id=object_id,
        name=name,
        tle1=str(tle1),
        tle2=str(tle2),
        inclination_deg=_to_float(record.get("inclination_deg") or record.get("inclinationDeg")),
        eccentricity=_to_float(record.get("eccentricity")),
        mean_motion=_to_float(record.get("mean_motion") or record.get("meanMotion")),
        arg_perigee=_to_float(record.get("arg_perigee") or record.get("argPerigee")),
        raan=_to_float(record.get("raan")),
        bstar=_to_float(record.get("bstar")),
        seed=_to_float(record.get("seed"), 1.0),
    )


def seeded_noise(seed: float, t_min: float, scale: float = 1.0) -> float:
    return (
        math.sin(t_min * 0.017 + seed * 1.13) * 0.58
        + math.cos(t_min * 0.013 + seed * 0.73) * 0.42
    ) * scale


def lat_lng_alt_to_xyz(lat_deg: float, lng_deg: float, alt_km: float) -> tuple[float, float, float]:
    lat_rad = math.radians(lat_deg)
    lng_rad = math.radians(lng_deg)
    r = EARTH_RADIUS_KM + alt_km

    x = r * math.cos(lat_rad) * math.cos(lng_rad)
    y = r * math.cos(lat_rad) * math.sin(lng_rad)
    z = r * math.sin(lat_rad)
    return x, y, z


def xyz_to_lat_lng_alt(x: float, y: float, z: float) -> tuple[float, float, float]:
    r = math.sqrt(x * x + y * y + z * z)
    lat = math.degrees(math.asin(z / r)) if r else 0.0
    lng = math.degrees(math.atan2(y, x))
    alt = r - EARTH_RADIUS_KM
    return lat, lng, alt


def _wrap_lng(lng_deg: float) -> float:
    return ((lng_deg + 180.0) % 360.0) - 180.0


def get_debris(debris_id: str) -> DebrisObject:
    for debris in load_debris_catalog():
        if debris.object_id == debris_id:
            return debris
    raise ValueError(f"Unknown debris id: {debris_id}")


def get_debris_payload() -> list[dict[str, object]]:
    payload = []
    for debris in load_debris_catalog():
        payload.append(
            {
                "id": debris.object_id,
                "name": debris.name,
                "tle": [debris.tle1, debris.tle2],
                "elements": {
                    "inclinationDeg": debris.inclination_deg,
                    "eccentricity": debris.eccentricity,
                    "meanMotion": debris.mean_motion,
                    "argPerigee": debris.arg_perigee,
                    "raan": debris.raan,
                    "bstar": debris.bstar,
                },
            }
        )
    return payload


def generate_baseline_trajectory(debris: DebrisObject, horizon_mins: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    base_alt = 380.0 + (debris.mean_motion - 14.0) * 25.0
    period_factor = 180.0 / debris.mean_motion

    for t in range(0, horizon_mins + 1, STEP_MINS):
        phase = (t / period_factor) * math.radians(120.0)
        inc_rad = math.radians(debris.inclination_deg)

        raw_lat = math.sin(phase + debris.seed) * math.degrees(inc_rad) * 0.98
        raw_lng = _wrap_lng(phase * 75.0 + debris.raan + debris.seed * 60.0)
        raw_alt = base_alt + seeded_noise(debris.seed, t, 14.0)

        drift_lat = seeded_noise(debris.seed + 1.5, t, 1.6) * min(1.7, t / 140.0)
        drift_lng = seeded_noise(debris.seed + 0.8, t, 2.2) * min(1.7, t / 120.0)
        drift_alt = seeded_noise(debris.seed + 2.7, t, 8.0) * min(1.9, t / 110.0)

        observed_lat = raw_lat - drift_lat
        observed_lng = _wrap_lng(raw_lng - drift_lng)
        observed_alt = raw_alt - drift_alt

        raw_x, raw_y, raw_z = lat_lng_alt_to_xyz(raw_lat, raw_lng, raw_alt)
        obs_x, obs_y, obs_z = lat_lng_alt_to_xyz(observed_lat, observed_lng, observed_alt)

        rows.append(
            {
                "minute": t,
                "raw": {
                    "lat": raw_lat,
                    "lng": raw_lng,
                    "altKm": raw_alt,
                    "x": raw_x,
                    "y": raw_y,
                    "z": raw_z,
                },
                "observed": {
                    "lat": observed_lat,
                    "lng": observed_lng,
                    "altKm": observed_alt,
                    "x": obs_x,
                    "y": obs_y,
                    "z": obs_z,
                },
            }
        )

    for idx, row in enumerate(rows):
        if idx == 0:
            next_row = rows[idx + 1] if len(rows) > 1 else row
            dt_seconds = STEP_MINS * 60.0
            vx = (next_row["raw"]["x"] - row["raw"]["x"]) / dt_seconds
            vy = (next_row["raw"]["y"] - row["raw"]["y"]) / dt_seconds
            vz = (next_row["raw"]["z"] - row["raw"]["z"]) / dt_seconds
        else:
            prev_row = rows[idx - 1]
            dt_seconds = STEP_MINS * 60.0
            vx = (row["raw"]["x"] - prev_row["raw"]["x"]) / dt_seconds
            vy = (row["raw"]["y"] - prev_row["raw"]["y"]) / dt_seconds
            vz = (row["raw"]["z"] - prev_row["raw"]["z"]) / dt_seconds

        row["raw"]["vx"] = vx
        row["raw"]["vy"] = vy
        row["raw"]["vz"] = vz

    return rows
