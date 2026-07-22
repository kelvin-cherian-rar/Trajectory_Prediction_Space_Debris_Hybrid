const EARTH_RADIUS_KM = 6371;
const CELESTRAK_GROUP = "cosmos-2251-debris";
const CELESTRAK_TLE_URL = `https://celestrak.org/NORAD/elements/gp.php?GROUP=${CELESTRAK_GROUP}&FORMAT=tle`;

const state = {
  debrisCatalog: [],
  selectedId: null,
  horizonMins: 180,
  showRaw: true,
  showCorrected: true,
  latestRows: [],
  latestMetrics: null,
  catalogSource: "",
};

const rawColor = "#e76f51";
const correctedColor = "#2a9d8f";
const truthColor = "#f4a261";

const elements = {
  select: document.getElementById("debris-select"),
  horizonSlider: document.getElementById("horizon-slider"),
  horizonOutput: document.getElementById("horizon-output"),
  rawToggle: document.getElementById("show-uncorrected"),
  correctedToggle: document.getElementById("show-corrected"),
  tleText: document.getElementById("tle-text"),
  catalogMeta: document.getElementById("catalog-meta"),
  rmseRaw: document.getElementById("rmse-raw"),
  rmseCorrected: document.getElementById("rmse-corrected"),
  maeRaw: document.getElementById("mae-raw"),
  maeCorrected: document.getElementById("mae-corrected")
};

const globeContainer = document.getElementById("globe");

const globe = Globe()(globeContainer)
  .globeImageUrl("https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg")
  .bumpImageUrl("https://unpkg.com/three-globe/example/img/earth-topology.png")
  .backgroundImageUrl("https://unpkg.com/three-globe/example/img/night-sky.png")
  .showAtmosphere(true)
  .atmosphereColor("#9ad1ff")
  .atmosphereAltitude(0.14)
  .lineHoverPrecision(0)
  .pointAltitude("alt")
  .pointRadius("size")
  .pointColor("color")
  .pointLabel((d) => d.label)
  .pathPointLat("lat")
  .pathPointLng("lng")
  .pathPointAlt("alt")
  .pathTransitionDuration(0)
  .pathStroke(0.85)
  .pathColor((d) => d.color)
  .pathDashLength((d) => d.dashLength)
  .pathDashGap((d) => d.dashGap)
  .pathDashAnimateTime((d) => d.dashAnimateMs);

globe.controls().autoRotate = true;
globe.controls().autoRotateSpeed = 0.55;
globe.controls().minDistance = 180;
globe.controls().maxDistance = 450;
globe.pointOfView({ lat: 18, lng: 15, altitude: 2.3 }, 1000);

function syncGlobeSize() {
  globe.width(globeContainer.clientWidth);
  globe.height(globeContainer.clientHeight);
}

syncGlobeSize();
window.addEventListener("resize", syncGlobeSize);

if (typeof ResizeObserver !== "undefined") {
  const resizeObserver = new ResizeObserver(syncGlobeSize);
  resizeObserver.observe(globeContainer);
}

function toGlobeAlt(altKm) {
  return altKm / EARTH_RADIUS_KM;
}

function formatKm(value) {
  return `${value.toFixed(2)} km`;
}

function parseTleExponent(field) {
  const text = String(field || "").trim();
  if (!text) {
    return 0;
  }

  const match = text.match(/^([+-]?)(\d+)([+-]\d+)$/);
  if (match) {
    const sign = match[1] === "-" ? -1 : 1;
    const mantissa = Number(`0.${match[2]}`);
    const exponent = Number(match[3]);
    return sign * mantissa * 10 ** exponent;
  }

  const numeric = Number(text.replace(/\s+/g, ""));
  return Number.isFinite(numeric) ? numeric : 0;
}

function parseCelestrakTleCatalog(text) {
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trimEnd())
    .filter((line) => line.trim().length > 0);

  const items = [];
  for (let index = 0; index + 2 < lines.length; index += 3) {
    const name = lines[index].trim();
    const tle1 = lines[index + 1].trim();
    const tle2 = lines[index + 2].trim();
    const catnr = Number.parseInt(tle2.slice(2, 7), 10);

    if (!Number.isFinite(catnr)) {
      continue;
    }

    items.push({
      id: `NORAD-${catnr}`,
      object_id: `NORAD-${catnr}`,
      name,
      tle1,
      tle2,
      inclination_deg: Number.parseFloat(tle2.slice(8, 16)),
      eccentricity: Number.parseFloat(`0.${tle2.slice(26, 33).trim()}`),
      mean_motion: Number.parseFloat(tle2.slice(52, 63)),
      arg_perigee: Number.parseFloat(tle2.slice(34, 42)),
      raan: Number.parseFloat(tle2.slice(17, 25)),
      bstar: parseTleExponent(tle1.slice(53, 61)),
      seed: (catnr % 1000) / 100,
    });
  }

  return items;
}

function buildGlobeData(rows) {
  const paths = [];
  const points = [];

  if (state.showRaw) {
    paths.push({
      id: "path-raw",
      points: rows.map((r) => ({ lat: r.raw.lat, lng: r.raw.lng, alt: toGlobeAlt(r.raw.altKm) })),
      color: rawColor,
      dashLength: 0.58,
      dashGap: 0.22,
      dashAnimateMs: 1700
    });
  }

  if (state.showCorrected) {
    paths.push({
      id: "path-corrected",
      points: rows.map((r) => ({ lat: r.corrected.lat, lng: r.corrected.lng, alt: toGlobeAlt(r.corrected.altKm) })),
      color: correctedColor,
      dashLength: 0.72,
      dashGap: 0.16,
      dashAnimateMs: 1250
    });
  }

  paths.push({
    id: "path-truth",
    points: rows.map((r) => ({ lat: r.observed.lat, lng: r.observed.lng, alt: toGlobeAlt(r.observed.altKm) })),
    color: truthColor,
    dashLength: 0.92,
    dashGap: 0.09,
    dashAnimateMs: 0
  });

  const latest = rows[rows.length - 1];

  if (state.showRaw) {
    points.push({
      lat: latest.raw.lat,
      lng: latest.raw.lng,
      alt: toGlobeAlt(latest.raw.altKm),
      size: 0.18,
      color: rawColor,
      label: "Raw SGP4"
    });
  }

  if (state.showCorrected) {
    points.push({
      lat: latest.corrected.lat,
      lng: latest.corrected.lng,
      alt: toGlobeAlt(latest.corrected.altKm),
      size: 0.18,
      color: correctedColor,
      label: "Corrected"
    });
  }

  points.push({
    lat: latest.observed.lat,
    lng: latest.observed.lng,
    alt: toGlobeAlt(latest.observed.altKm),
    size: 0.18,
    color: truthColor,
    label: "Observed truth"
  });

  return { paths, points };
}

function renderChart(rows, metrics) {
  const minutes = rows.map((r) => r.minute);

  Plotly.newPlot(
    "error-chart",
    [
      {
        x: minutes,
        y: metrics.rawErrors,
        type: "scatter",
        mode: "lines",
        name: "Raw SGP4 Error",
        line: { color: rawColor, width: 2.2 }
      },
      {
        x: minutes,
        y: metrics.correctedErrors,
        type: "scatter",
        mode: "lines",
        name: "Corrected Error",
        line: { color: correctedColor, width: 2.4 }
      }
    ],
    {
      margin: { t: 12, r: 20, b: 44, l: 52 },
      paper_bgcolor: "rgba(0,0,0,0)",
      plot_bgcolor: "rgba(4, 14, 25, 0.38)",
      xaxis: {
        title: "Time Since Epoch (min)",
        gridcolor: "rgba(255,255,255,0.08)",
        color: "#ccdae9"
      },
      yaxis: {
        title: "Position Error (km)",
        gridcolor: "rgba(255,255,255,0.08)",
        color: "#ccdae9"
      },
      legend: {
        orientation: "h",
        x: 0,
        y: 1.13,
        font: { color: "#dce7f2", size: 11 }
      }
    },
    { responsive: true, displayModeBar: false }
  );
}

function updateMetrics(metrics) {
  elements.rmseRaw.textContent = formatKm(metrics.rmseRaw);
  elements.rmseCorrected.textContent = formatKm(metrics.rmseCorrected);
  elements.maeRaw.textContent = formatKm(metrics.maeRaw);
  elements.maeCorrected.textContent = formatKm(metrics.maeCorrected);
}

async function fetchDebrisCatalog() {
  try {
    const response = await fetch(CELESTRAK_TLE_URL);
    if (!response.ok) {
      throw new Error(`CelesTrak fetch failed: ${response.status}`);
    }

    const text = await response.text();
    const items = parseCelestrakTleCatalog(text);
    state.catalogSource = `Live CelesTrak feed: ${CELESTRAK_GROUP}`;
    if (elements.catalogMeta) {
      elements.catalogMeta.textContent = `${items.length} debris objects loaded from ${state.catalogSource}`;
    }
    return items;
  } catch (error) {
    console.warn("Falling back to local catalog:", error);
    const response = await fetch("/api/debris");
    if (!response.ok) {
      throw new Error(`Failed to load debris catalog: ${response.status}`);
    }

    const payload = await response.json();
    state.catalogSource = "Local fallback catalog";
    if (elements.catalogMeta) {
      elements.catalogMeta.textContent = `${payload.items.length} objects loaded from ${state.catalogSource}`;
    }
    return payload.items;
  }
}

async function fetchTrajectory() {
  const selectedDebris = state.debrisCatalog.find((item) => item.id === state.selectedId);
  const response = await fetch("/api/trajectory", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      horizon_mins: state.horizonMins,
      debris: selectedDebris,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to load trajectory: ${response.status}`);
  }

  return response.json();
}

async function updateView() {
  if (!state.selectedId) {
    return;
  }

  try {
    const payload = await fetchTrajectory();
    const rows = payload.rows;
    const metrics = payload.metrics;
    const debris = payload.debris;

    state.latestRows = rows;
    state.latestMetrics = metrics;

    const globeData = buildGlobeData(rows);
    globe.pathsData(globeData.paths).pointsData(globeData.points);

    updateMetrics(metrics);
    renderChart(rows, metrics);

    elements.tleText.textContent = `${debris.tle[0]}\n${debris.tle[1]}`;

    if (payload.modelStatus && payload.modelStatus.warnings && payload.modelStatus.warnings.length > 0) {
      console.warn("Model status warnings:", payload.modelStatus.warnings);
    }
  } catch (error) {
    console.error(error);
  }
}

function rerenderFromState() {
  if (!state.latestRows.length || !state.latestMetrics) {
    return;
  }

  const globeData = buildGlobeData(state.latestRows);
  globe.pathsData(globeData.paths).pointsData(globeData.points);
  renderChart(state.latestRows, state.latestMetrics);
}

function initializeControls() {
  elements.select.addEventListener("change", async (event) => {
    state.selectedId = event.target.value;
    await updateView();
  });

  elements.horizonSlider.addEventListener("input", async (event) => {
    state.horizonMins = Number(event.target.value);
    elements.horizonOutput.textContent = String(state.horizonMins);
    await updateView();
  });

  elements.rawToggle.addEventListener("change", (event) => {
    state.showRaw = event.target.checked;
    rerenderFromState();
  });

  elements.correctedToggle.addEventListener("change", (event) => {
    state.showCorrected = event.target.checked;
    rerenderFromState();
  });
}

async function bootstrap() {
  initializeControls();

  const catalog = await fetchDebrisCatalog();
  state.debrisCatalog = catalog;

  for (const debris of catalog) {
    const option = document.createElement("option");
    option.value = debris.id;
    option.textContent = `${debris.name} (${debris.id})`;
    elements.select.appendChild(option);
  }

  if (catalog.length > 0) {
    state.selectedId = catalog[0].id;
    elements.select.value = state.selectedId;
  }

  await updateView();
}

bootstrap().catch((error) => {
  console.error("Bootstrap failed:", error);
});
