import { readFileSync, writeFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const path = join(
  dirname(fileURLToPath(import.meta.url)),
  "..",
  "..",
  "flows",
  "821-huawei-energy-status.json"
);

const PV_FORECAST_FN = `
const PANELS_S1 = 10;
const PANELS_S2 = 10;
const G_REF = 1000;
const EAST_PEAK = 9.5;
const WEST_PEAK = 15.5;
const ORIENT_SIGMA = 2.5;
const SYS_EFF = 0.85;

function orientationWeights(localHour) {
  const wEast = Math.exp(-Math.pow(localHour - EAST_PEAK, 2) / (2 * ORIENT_SIGMA * ORIENT_SIGMA));
  const wWest = Math.exp(-Math.pow(localHour - WEST_PEAK, 2) / (2 * ORIENT_SIGMA * ORIENT_SIGMA));
  return { wEast, wWest };
}

function resolveForecast(explicit) {
  return explicit
    || flow.get('huawei_solar_forecast')
    || flow.get('victron_solar_forecast')
    || null;
}

function resolveRadiationWm2(forecast) {
  const scalar = flow.get('huawei_forecast_radiation_wm2');
  if (scalar != null && scalar !== '') {
    const n = Number(scalar);
    if (!Number.isNaN(n)) return n;
  }
  if (forecast == null) return null;
  if (typeof forecast === 'number') return forecast;
  if (forecast.shortwave_radiation_wm2 != null) {
    const n = Number(forecast.shortwave_radiation_wm2);
    return Number.isNaN(n) ? null : n;
  }
  if (forecast.radiation_wm2 != null) {
    const n = Number(forecast.radiation_wm2);
    return Number.isNaN(n) ? null : n;
  }
  return null;
}

function estimatePvFromRadiation(radiationWm2, ratedPowerW, localHour) {
  const { wEast, wWest } = orientationWeights(localHour);
  const wSum = wEast + wWest;
  if (radiationWm2 == null || radiationWm2 <= 0 || !ratedPowerW) {
    return { total_w: 0, string1_w: 0, string2_w: 0, w_east: wEast, w_west: wWest, g_frac: 0 };
  }
  const gFrac = radiationWm2 / G_REF;
  const total = ratedPowerW * gFrac * SYS_EFF;
  if (wSum <= 0) {
    return {
      total_w: Math.round(total),
      string1_w: Math.round(total / 2),
      string2_w: Math.round(total / 2),
      w_east: wEast,
      w_west: wWest,
      g_frac: Math.round(gFrac * 10000) / 10000
    };
  }
  return {
    total_w: Math.round(total),
    string1_w: Math.round(total * wWest / wSum),
    string2_w: Math.round(total * wEast / wSum),
    w_east: Math.round(wEast * 1000) / 1000,
    w_west: Math.round(wWest * 1000) / 1000,
    g_frac: Math.round(gFrac * 10000) / 10000
  };
}

function localHourBucharest(d) {
  const parts = new Intl.DateTimeFormat('en-GB', {
    timeZone: 'Europe/Bucharest',
    hour: 'numeric',
    minute: 'numeric',
    hour12: false
  }).formatToParts(d || new Date());
  const h = Number(parts.find(p => p.type === 'hour')?.value || 0);
  const m = Number(parts.find(p => p.type === 'minute')?.value || 0);
  return h + m / 60;
}

function averagePvW(hist, maxSamples) {
  const samples = (hist || []).filter(p => {
    const w = Number(p.dc ?? p.active);
    return !Number.isNaN(w) && w > 0;
  }).slice(-(maxSamples || 96));
  if (!samples.length) return null;
  return Math.round(samples.reduce((sum, p) => sum + Number(p.dc ?? p.active), 0) / samples.length);
}

function computePvForecast(data, hist, forecastIn) {
  const pv = data.pv || {};
  const v1 = Number(pv.string1_voltage_v);
  const i1 = Number(pv.string1_current_a);
  const v2 = Number(pv.string2_voltage_v);
  const i2 = Number(pv.string2_current_a);
  const s1 = (!Number.isNaN(v1) && !Number.isNaN(i1)) ? v1 * i1 : null;
  const s2 = (!Number.isNaN(v2) && !Number.isNaN(i2)) ? v2 * i2 : null;
  let totalAct = null;
  if (s1 != null && s2 != null) totalAct = s1 + s2;
  else if (pv.input_power_w != null) totalAct = Number(pv.input_power_w);
  else if (data.inverter?.active_power_w != null) totalAct = Number(data.inverter.active_power_w);

  const rated = Number(data.device?.rated_power_w) || 6000;
  const forecast = resolveForecast(forecastIn);
  const G = resolveRadiationWm2(forecast);
  const localHour = localHourBucharest(new Date());
  const expected = estimatePvFromRadiation(G, rated, localHour);
  const avgPv = averagePvW(hist);
  let performancePct = null;
  if (expected.total_w > 0 && totalAct != null) {
    performancePct = Math.round((totalAct / expected.total_w) * 100);
  }
  return {
    formula: 'P_est = P_rated × (G/1000) × η; split total by east/west orientation weights',
    panels: { string1_west: PANELS_S1, string2_east: PANELS_S2, total: PANELS_S1 + PANELS_S2 },
    radiation_wm2: G,
    is_day: forecast?.is_day,
    local_hour: Math.round(localHour * 10) / 10,
    actual: {
      string1_w: s1 != null ? Math.round(s1) : null,
      string2_w: s2 != null ? Math.round(s2) : null,
      total_w: totalAct != null ? Math.round(totalAct) : null
    },
    expected,
    avg_pv_w: avgPv,
    performance_pct: performancePct
  };
}
`.trim();

const STORE_TAIL = `
if (!msg.payload || typeof msg.payload !== 'object') return null;
flow.set('huawei_solar_forecast', msg.payload);
if (msg.payload.shortwave_radiation_wm2 != null) {
  flow.set('huawei_forecast_radiation_wm2', msg.payload.shortwave_radiation_wm2);
}
const last = flow.get('last_huawei_status');
if (!last) return null;
const hist = flow.get('huawei_week_history') || [];
const data = { ...last, week_chart: hist, forecast_solar: msg.payload };
data.pv_forecast = computePvForecast(data, hist, msg.payload);
return {
  payload: data,
  metadata: flow.get('huawei_energy_metadata') || {}
};`.trim();

const PROCESS_TAIL = `
const data = msg.payload;
if (!data || typeof data !== 'object' || !data.timestamp) {
    node.warn('Invalid Huawei status payload');
    return null;
}

const receivedMs = Date.now();
let reportMs;
try { reportMs = new Date(data.timestamp).getTime(); } catch (e) { reportMs = receivedMs; }

flow.set('last_huawei_status', data);

const WEEK_MS = 7 * 24 * 60 * 60 * 1000;
const BUCKET_MS = 15 * 60 * 1000;
const point = {
    t: reportMs,
    active: data.inverter?.active_power_w,
    dc: data.pv?.input_power_w,
    yield: data.inverter?.daily_yield_kwh
};
let hist = flow.get('huawei_week_history') || [];
const bucket = Math.floor(reportMs / BUCKET_MS) * BUCKET_MS;
if (hist.length && hist[hist.length - 1].bucket === bucket) {
    hist[hist.length - 1] = { bucket, ...point };
} else {
    hist.push({ bucket, ...point });
}
const cutoff = Date.now() - WEEK_MS;
hist = hist.filter(h => h.t >= cutoff);
flow.set('huawei_week_history', hist);
data.week_chart = hist;

const forecast = resolveForecast(flow.get('huawei_solar_forecast'));
if (forecast) data.forecast_solar = forecast;
data.pv_forecast = computePvForecast(data, hist, forecast);

global.set('huawei_energy_state', {
    ...data,
    lastReportedMs: reportMs,
    receivedAtMs: receivedMs
});

const metaKey = 'huawei_energy_metadata';
let meta = flow.get(metaKey) || { lastReportedMs: null };
meta.lastReportedMs = reportMs;
flow.set(metaKey, meta);
msg.payload = data;
msg.metadata = meta;

const ap = data.inverter?.active_power_w;
node.status({ fill: 'green', shape: 'dot', text: \`PV \${ap != null ? ap : '?'} W · est \${data.pv_forecast?.expected?.total_w ?? '?'} W\` });
return msg;`.trim();

const REFRESH_TAIL = `
const last = flow.get('last_huawei_status');
if (!last) return null;
const hist = flow.get('huawei_week_history') || [];
const forecast = resolveForecast(flow.get('huawei_solar_forecast'));
const data = { ...last, week_chart: hist };
if (forecast) data.forecast_solar = forecast;
data.pv_forecast = computePvForecast(data, hist, forecast);
return {
    payload: data,
    metadata: flow.get('huawei_energy_metadata') || {}
};`.trim();

const SCALAR_TAIL = `
const n = Number(msg.payload);
if (!Number.isNaN(n)) flow.set('huawei_forecast_radiation_wm2', n);
const last = flow.get('last_huawei_status');
if (!last) return null;
const hist = flow.get('huawei_week_history') || [];
const forecast = resolveForecast(flow.get('huawei_solar_forecast'));
const data = { ...last, week_chart: hist };
if (forecast) data.forecast_solar = forecast;
data.pv_forecast = computePvForecast(data, hist, forecast);
return {
  payload: data,
  metadata: flow.get('huawei_energy_metadata') || {}
};`.trim();

const data = JSON.parse(readFileSync(path, "utf8"));

data.find((n) => n.id === "func_huawei_process_status").func = `${PV_FORECAST_FN}\n${PROCESS_TAIL}`;
data.find((n) => n.id === "func_huawei_refresh_dashboard").func = `${PV_FORECAST_FN}\n${REFRESH_TAIL}`;
data.find((n) => n.id === "func_huawei_store_forecast").func = `${PV_FORECAST_FN}\n${STORE_TAIL}`;

if (!data.find((n) => n.id === "mqtt_in_huawei_forecast_radiation")) {
  data.push(
    {
      id: "mqtt_in_huawei_forecast_radiation",
      type: "mqtt in",
      z: "tab_dashboard",
      name: "Solar radiation scalar",
      topic: "energy/victron/forecast/solar/radiation_wm2",
      qos: "1",
      datatype: "auto-detect",
      broker: "mqtt_broker_local",
      nl: false,
      rap: true,
      rh: 0,
      inputs: 0,
      x: 200,
      y: 840,
      wires: [["func_huawei_store_forecast_radiation"]],
    },
    {
      id: "func_huawei_store_forecast_radiation",
      type: "function",
      z: "tab_dashboard",
      name: "Store radiation scalar",
      func: `${PV_FORECAST_FN}\n${SCALAR_TAIL}`,
      outputs: 1,
      noerr: 0,
      initialize: "",
      finalize: "",
      libs: [],
      x: 470,
      y: 840,
      wires: [["template_huawei_energy_dashboard"]],
    }
  );
} else {
  data.find((n) => n.id === "func_huawei_store_forecast_radiation").func =
    `${PV_FORECAST_FN}\n${SCALAR_TAIL}`;
}

writeFileSync(path, `${JSON.stringify(data, null, 4)}\n`);

// quick sanity check with sample inputs
const G = 650;
const rated = 6000;
const localHour = 10.5;
const wEast = Math.exp(-Math.pow(localHour - 9.5, 2) / (2 * 2.5 * 2.5));
const wWest = Math.exp(-Math.pow(localHour - 15.5, 2) / (2 * 2.5 * 2.5));
const wSum = wEast + wWest;
const total = Math.round(rated * (G / 1000) * 0.85);
console.log("Sanity:", { G, total, string1: Math.round(total * wEast / wSum) });

console.log("Fixed PV forecast formula + radiation resolution");
