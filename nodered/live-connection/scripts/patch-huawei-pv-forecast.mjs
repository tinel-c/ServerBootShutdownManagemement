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

function estimatePvFromRadiation(radiationWm2, ratedPowerW, localHour) {
  const { wEast, wWest } = orientationWeights(localHour);
  const wSum = wEast + wWest;
  if (!radiationWm2 || radiationWm2 <= 0 || !ratedPowerW || wSum <= 0) {
    return { total_w: 0, string1_w: 0, string2_w: 0, w_east: wEast, w_west: wWest, g_frac: 0 };
  }
  const gFrac = radiationWm2 / G_REF;
  const total = ratedPowerW * gFrac * SYS_EFF * Math.min(1, wSum);
  return {
    total_w: Math.round(total),
    string1_w: Math.round(total * wEast / wSum),
    string2_w: Math.round(total * wWest / wSum),
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

function computePvForecast(data, hist, forecast) {
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
  const G = forecast?.shortwave_radiation_wm2 != null ? Number(forecast.shortwave_radiation_wm2) : null;
  const localHour = localHourBucharest(new Date());
  const expected = estimatePvFromRadiation(G, rated, localHour);
  const avgPv = averagePvW(hist);
  let performancePct = null;
  if (expected.total_w > 0 && totalAct != null) {
    performancePct = Math.round((totalAct / expected.total_w) * 100);
  }
  return {
    formula: 'P_est = P_rated × (G/1000) × η × min(1,w_east+w_west); split by east/west weights',
    panels: { string1_east: PANELS_S1, string2_west: PANELS_S2, total: PANELS_S1 + PANELS_S2 },
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

const PROCESS_APPEND = `
const forecast = flow.get('huawei_solar_forecast');
if (forecast) data.forecast_solar = forecast;
data.pv_forecast = computePvForecast(data, hist, forecast);
`;

const PROCESS_FUNC = `${PV_FORECAST_FN}
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
${PROCESS_APPEND}
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
node.status({ fill: 'green', shape: 'dot', text: \`PV \${ap != null ? ap : '?'} W\` });
return msg;`;

const REFRESH_FUNC = `${PV_FORECAST_FN}
const last = flow.get('last_huawei_status');
if (!last) return null;
const hist = flow.get('huawei_week_history') || [];
const forecast = flow.get('huawei_solar_forecast');
const data = { ...last, week_chart: hist };
if (forecast) data.forecast_solar = forecast;
data.pv_forecast = computePvForecast(data, hist, forecast);
return {
    payload: data,
    metadata: flow.get('huawei_energy_metadata') || {}
};`;

const STORE_FORECAST_FUNC = `if (!msg.payload || typeof msg.payload !== 'object') return null;
flow.set('huawei_solar_forecast', msg.payload);
const last = flow.get('last_huawei_status');
if (!last) return null;
const hist = flow.get('huawei_week_history') || [];
const data = { ...last, week_chart: hist, forecast_solar: msg.payload };
data.pv_forecast = computePvForecast(data, hist, msg.payload);
return {
    payload: data,
    metadata: flow.get('huawei_energy_metadata') || {}
};`;

const FORECAST_CARD = `  <div v-if="pvForecast" style="margin-bottom:16px;padding:14px;border-radius:14px;background:rgba(0,0,0,0.28);border:1px solid rgba(251,191,36,0.3);">
    <div style="display:flex;flex-wrap:wrap;gap:10px;justify-content:space-between;margin-bottom:10px;">
      <div style="font-weight:700;color:#fde047;">PV forecast · 10 west (S1) + 10 east (S2)</div>
      <div style="font-size:0.8em;color:#94a3b8;">Open-Meteo · {{ pvForecastRadiation }}</div>
    </div>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;font-size:0.85em;margin-bottom:10px;">
      <div style="padding:10px;border-radius:10px;background:rgba(255,255,255,0.04);">
        <div style="color:#94a3b8;font-size:0.75em;text-transform:uppercase;">Avg PV (24h)</div>
        <div style="font-weight:700;font-size:1.2em;">{{ pvForecastAvg }}</div>
      </div>
      <div style="padding:10px;border-radius:10px;background:rgba(255,255,255,0.04);">
        <div style="color:#94a3b8;font-size:0.75em;text-transform:uppercase;">Performance</div>
        <div style="font-weight:700;font-size:1.2em;" :style="{ color: pvForecastPerformanceColor }">{{ pvForecastPerformance }}</div>
      </div>
      <div style="padding:10px;border-radius:10px;background:rgba(255,255,255,0.04);">
        <div style="color:#94a3b8;font-size:0.75em;text-transform:uppercase;">Orientation</div>
        <div style="font-weight:600;">E {{ pvForecastWEast }} · W {{ pvForecastWWest }}</div>
      </div>
    </div>
    <table style="width:100%;border-collapse:collapse;font-size:0.85em;">
      <thead>
        <tr style="color:#94a3b8;text-align:left;">
          <th style="padding:6px 8px;"></th>
          <th style="padding:6px 8px;">Expected</th>
          <th style="padding:6px 8px;">Actual (V×I)</th>
        </tr>
      </thead>
      <tbody>
        <tr style="border-top:1px solid rgba(255,255,255,0.08);">
          <td style="padding:6px 8px;color:#fdba74;">String 1 · west</td>
          <td style="padding:6px 8px;font-weight:600;">{{ pvForecastExpS1 }}</td>
          <td style="padding:6px 8px;font-weight:600;">{{ pvForecastActS1 }}</td>
        </tr>
        <tr style="border-top:1px solid rgba(255,255,255,0.08);">
          <td style="padding:6px 8px;color:#fdba74;">String 2 · east</td>
          <td style="padding:6px 8px;font-weight:600;">{{ pvForecastExpS2 }}</td>
          <td style="padding:6px 8px;font-weight:600;">{{ pvForecastActS2 }}</td>
        </tr>
        <tr style="border-top:1px solid rgba(255,255,255,0.08);">
          <td style="padding:6px 8px;color:#fde68a;">Total</td>
          <td style="padding:6px 8px;font-weight:700;">{{ pvForecastExpTotal }}</td>
          <td style="padding:6px 8px;font-weight:700;">{{ pvForecastActTotal }}</td>
        </tr>
      </tbody>
    </table>
    <div style="font-size:0.7em;color:#64748b;margin-top:8px;">{{ pvForecastFormula }}</div>
  </div>
`;

const COMPUTED_APPEND = `
    pvForecast() { return this.p.pv_forecast || null; },
    pvForecastRadiation() {
      const g = this.pvForecast?.radiation_wm2;
      return g != null ? Math.round(g) + ' W/m²' : '—';
    },
    pvForecastAvg() {
      const v = this.pvForecast?.avg_pv_w;
      return v != null ? v + ' W' : '—';
    },
    pvForecastPerformance() {
      const v = this.pvForecast?.performance_pct;
      return v != null ? v + '%' : '—';
    },
    pvForecastPerformanceColor() {
      const v = this.pvForecast?.performance_pct;
      if (v == null) return '#94a3b8';
      if (v >= 90) return '#4ade80';
      if (v >= 70) return '#fde047';
      return '#fb923c';
    },
    pvForecastWEast() { return this.pvForecast?.expected?.w_east ?? '—'; },
    pvForecastWWest() { return this.pvForecast?.expected?.w_west ?? '—'; },
    pvForecastFormula() { return this.pvForecast?.formula || ''; },
    pvForecastExpS1() { return this.formatW(this.pvForecast?.expected?.string1_w); },
    pvForecastExpS2() { return this.formatW(this.pvForecast?.expected?.string2_w); },
    pvForecastExpTotal() { return this.formatW(this.pvForecast?.expected?.total_w); },
    pvForecastActS1() { return this.formatW(this.pvForecast?.actual?.string1_w); },
    pvForecastActS2() { return this.formatW(this.pvForecast?.actual?.string2_w); },
    pvForecastActTotal() { return this.formatW(this.pvForecast?.actual?.total_w); },`;

const data = JSON.parse(readFileSync(path, "utf8"));

const processNode = data.find((n) => n.id === "func_huawei_process_status");
processNode.func = PROCESS_FUNC;

const refreshNode = data.find((n) => n.id === "func_huawei_refresh_dashboard");
refreshNode.func = REFRESH_FUNC;

if (!data.find((n) => n.id === "mqtt_in_huawei_forecast")) {
  data.push(
    {
      id: "mqtt_in_huawei_forecast",
      type: "mqtt in",
      z: "tab_dashboard",
      name: "Solar forecast (Open-Meteo)",
      topic: "energy/victron/forecast/solar/current",
      qos: "1",
      datatype: "json",
      broker: "mqtt_broker_local",
      nl: false,
      rap: true,
      rh: 0,
      inputs: 0,
      x: 200,
      y: 780,
      wires: [["func_huawei_store_forecast"]],
    },
    {
      id: "func_huawei_store_forecast",
      type: "function",
      z: "tab_dashboard",
      name: "Store forecast + refresh PV model",
      func: `${PV_FORECAST_FN}\n${STORE_FORECAST_FUNC.split(PV_FORECAST_FN)[1] || STORE_FORECAST_FUNC}`,
      outputs: 1,
      noerr: 0,
      initialize: "",
      finalize: "",
      libs: [],
      x: 480,
      y: 780,
      wires: [["template_huawei_energy_dashboard"]],
    }
  );
} else {
  const storeNode = data.find((n) => n.id === "func_huawei_store_forecast");
  storeNode.func = `${PV_FORECAST_FN}\n${STORE_FORECAST_FUNC.replace(PV_FORECAST_FN, "").trim()}`;
}

const comment = data.find((n) => n.id === "huawei_energy_comment");
comment.info =
  "## Huawei Energy Status Dashboard\n\n**Flow 821** — SUN2000 live metrics, PV forecast model, 7-day chart.\n\nMQTT: `energy/huawei/status`, `energy/victron/forecast/solar/current`\nGlobal: `huawei_energy_state`";

const template = data.find((n) => n.id === "template_huawei_energy_dashboard");
let format = template.format;

const anchor = `  <div v-if="weekChart.length" class="energy-chart-wrap"`;
if (!format.includes("PV forecast · 10 east")) {
  format = format.replace(anchor, `${FORECAST_CARD}\n${anchor}`);
}

if (!format.includes("pvForecast()")) {
  format = format.replace(
    "    chartXTicks() {",
    `${COMPUTED_APPEND}\n    chartXTicks() {`
  );
}

template.format = format;

writeFileSync(path, `${JSON.stringify(data, null, 4)}\n`);
console.log("Patched 821 with PV forecast model");
