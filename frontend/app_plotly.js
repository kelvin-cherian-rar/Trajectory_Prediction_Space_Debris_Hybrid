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
  catalogSource: ""
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
  maeCorrected: document.getElementById("mae-corrected"),
  globe: document.getElementById("globe")
};

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
      seed: (catnr % 1000) / 100
    });
  }

  return items;
}

function buildGlobeTraces(rows) {
  const traces = [];

  if (state.showRaw) {
    traces.push({
      type: "scattergeo",
      mode: "lines",
      name: "Raw SGP4",
      lon: rows.map((row) => row.raw.lng),
      lat: rows.map((row) => row.raw.lat),
      line: { color: rawColor, width: 2.4 },
      hovertemplate: "Raw SGP4<br>Lat %{lat:.2f}°<br>Lng %{lon:.2f}°<br>Alt %{customdata:.1f} km<extra></extra>",
      customdata: rows.map((row) => row.raw.altKm)
    });
  }

  if (state.showCorrected) {
    traces.push({
      type: "scattergeo",
      mode: "lines",
      name: "Corrected",
      lon: rows.map((row) => row.corrected.lng),
      lat: rows.map((row) => row.corrected.lat),
      line: { color: correctedColor, width: 2.6 },
      hovertemplate: "Corrected<br>Lat %{lat:.2f}°<br>Lng %{lon:.2f}°<br>Alt %{customdata:.1f} km<extra></extra>",
      customdata: rows.map((row) => row.corrected.altKm)
    });
  }

  traces.push({
    type: "scattergeo",
    mode: "lines",
    name: "Observed",
    lon: rows.map((row) => row.observed.lng),
    lat: rows.map((row) => row.observed.lat),
    line: { color: truthColor, width: 2.2, dash: "dot" },
    hovertemplate: "Observed<br>Lat %{lat:.2f}°<br>Lng %{lon:.2f}°<br>Alt %{customdata:.1f} km<extra></extra>",
    customdata: rows.map((row) => row.observed.altKm)
  });

  const latest = rows[rows.length - 1];
  if (state.showRaw) {
    traces.push({
      type: "scattergeo",
      mode: "markers",
      name: "Raw end",
      lon: [latest.raw.lng],
      lat: [latest.raw.lat],
      marker: { size: 10, color: rawColor, line: { color: "#ffffff", width: 0.5 } },
      hovertemplate: "Raw end<extra></extra>"
    });
  }

  if (state.showCorrected) {
    traces.push({
      type: "scattergeo",
      mode: "markers",
      name: "Corrected end",
      lon: [latest.corrected.lng],
      lat: [latest.corrected.lat],
      marker: { size: 10, color: correctedColor, line: { color: "#ffffff", width: 0.5 } },
      hovertemplate: "Corrected end<extra></extra>"
    });
  }

  traces.push({
    type: "scattergeo",
    mode: "markers",
    name: "Observed end",
    lon: [latest.observed.lng],
    lat: [latest.observed.lat],
    marker: { size: 10, color: truthColor, line: { color: "#ffffff", width: 0.5 } },
    hovertemplate: "Observed end<extra></extra>"
  });

  return traces;
}

function renderGlobe(rows) {
  const traces = buildGlobeTraces(rows);
  const layout = {
    margin: { t: 0, r: 0, b: 0, l: 0 },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    showlegend: true,
    legend: {
      orientation: "h",
      x: 0.02,
      y: 0.98,
      font: { color: "#dce7f2", size: 11 },
      bgcolor: "rgba(6, 18, 31, 0.72)",
      bordercolor: "rgba(255,255,255,0.12)",
      borderwidth: 1
    },
    geo: {
      projection: { type: "orthographic", rotation: { lon: 20, lat: 12, roll: 0 } },
      showframe: false,
      showland: true,
      landcolor: "#1b3450",
      showocean: true,
      oceancolor: "#06121f",
      showlakes: true,
      lakecolor: "#06121f",
      showcoastlines: true,
      coastlinecolor: "#6e8daa",
      showcountries: false,
      bgcolor: "rgba(0,0,0,0)",
      lataxis: { showgrid: true, gridcolor: "rgba(255,255,255,0.08)", dtick: 30 },
      lonaxis: { showgrid: true, gridcolor: "rgba(255,255,255,0.08)", dtick: 30 }
    }
  };

  return Plotly.react(elements.globe, traces, layout, { responsive: true, displayModeBar: false });
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
    })
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

    await renderGlobe(rows);
    renderChart(rows, metrics);
    updateMetrics(metrics);

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

  renderGlobe(state.latestRows);
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
  window.addEventListener("resize", () => {
    Plotly.Plots.resize(elements.globe);
  });
}

bootstrap().catch((error) => {
  console.error("Bootstrap failed:", error);
});
