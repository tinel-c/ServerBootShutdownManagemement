#!/usr/bin/env python3
"""Regenerate 811-victron-energy-status.json with week chart and discretionary controls."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "811-victron-energy-status.json"

PROCESS_FUNC = r"""const data = msg.payload;
if (!data || typeof data !== 'object' || !data.timestamp) {
    node.warn('Invalid Victron status payload');
    return null;
}

const receivedMs = Date.now();
let reportMs;
try {
    reportMs = new Date(data.timestamp).getTime();
} catch (e) {
    reportMs = receivedMs;
}

flow.set('last_victron_status', data);
const forecast = flow.get('victron_solar_forecast');
if (forecast) data.forecast_solar = forecast;
const forecastDaily = flow.get('victron_solar_forecast_daily');
if (forecastDaily) data.forecast_daily = forecastDaily;

const WEEK_MS = 7 * 24 * 60 * 60 * 1000;
const BUCKET_MS = 15 * 60 * 1000;
const auto = data.automation || {};
const point = {
    t: reportMs,
    soc: data.battery?.soc_pct,
    grid: data.grid?.power_l1_w,
    pv: auto.pv_power_w ?? data.pv?.ac_output_l1_w,
    load: data.load?.consumption_l1_w,
    battP: data.battery?.power_w,
    headroom: auto.headroom_w,
    invOut: data.inverter?.ac_out_power_l1_w,
    invIn: data.inverter?.ac_in_power_l1_w,
    dcV: data.inverter?.dc_voltage_v
};
let hist = flow.get('victron_week_history') || [];
const bucket = Math.floor(reportMs / BUCKET_MS) * BUCKET_MS;
if (hist.length && hist[hist.length - 1].bucket === bucket) {
    hist[hist.length - 1] = { bucket, ...point };
} else {
    hist.push({ bucket, ...point });
}
const cutoff = Date.now() - WEEK_MS;
hist = hist.filter(h => h.t >= cutoff);
flow.set('victron_week_history', hist);
data.week_chart = hist;
data.discretionary_load = flow.get('victron_discretionary_load') || { enabled: false, updated_at: null, source: null };

global.set('victron_energy_state', {
    ...data,
    lastReportedMs: reportMs,
    receivedAtMs: receivedMs
});

const metaKey = 'victron_energy_metadata';
let meta = flow.get(metaKey) || {
    lastReportedMs: null,
    lastInverterState: 'Unknown',
    previousInverterState: 'Unknown',
    lastChangedMs: null
};
meta.lastReportedMs = reportMs;
const invState = (data.inverter && data.inverter.state) ? data.inverter.state : 'Unknown';
if (invState !== meta.lastInverterState) {
    meta.previousInverterState = meta.lastInverterState;
    meta.lastInverterState = invState;
    meta.lastChangedMs = reportMs;
}
flow.set(metaKey, meta);
msg.payload = data;
msg.metadata = meta;

const soc = data.battery && data.battery.soc_pct;
node.status({ fill: auto.can_add_load ? 'green' : 'yellow', shape: 'dot', text: `SoC ${soc != null ? soc : '?'}% | headroom ${auto.headroom_w != null ? auto.headroom_w : '?'}W` });
return msg;"""

DISC_FUNC = r"""const p = msg.payload;
if (!p || typeof p !== 'object' || !p.action) return [null, null, null];
const enabled = p.action === 'start';
const state = {
    enabled,
    action: p.action,
    source: p.source || 'dashboard',
    updated_at: new Date().toISOString(),
    headroom_w: flow.get('last_victron_status')?.automation?.headroom_w ?? null
};
flow.set('victron_discretionary_load', state);
const cmdTopic = enabled
    ? 'energy/victron/command/discretionary/start'
    : 'energy/victron/command/discretionary/stop';
const cmdPayload = JSON.stringify({
    action: p.action,
    source: 'nodered',
    timestamp: state.updated_at,
    enabled
});
const statePayload = JSON.stringify(state);
const last = flow.get('last_victron_status');
let refresh = null;
if (last) {
    refresh = {
        payload: {
            ...last,
            discretionary_load: state,
            week_chart: flow.get('victron_week_history') || [],
            forecast_solar: flow.get('victron_solar_forecast') || null,
            forecast_daily: flow.get('victron_solar_forecast_daily') || null
        },
        metadata: flow.get('victron_energy_metadata') || {}
    };
}
return [
    { topic: cmdTopic, payload: cmdPayload },
    { topic: 'energy/victron/automation/discretionary_load/state', payload: statePayload },
    refresh
];"""

REFRESH_FUNC = r"""const last = flow.get('last_victron_status');
if (!last) return null;
const data = { ...last };
data.discretionary_load = flow.get('victron_discretionary_load') || { enabled: false };
data.week_chart = flow.get('victron_week_history') || [];
const forecast = flow.get('victron_solar_forecast');
if (forecast) data.forecast_solar = forecast;
const forecastDaily = flow.get('victron_solar_forecast_daily');
if (forecastDaily) data.forecast_daily = forecastDaily;
return { payload: data, metadata: flow.get('victron_energy_metadata') || {} };"""

TEMPLATE = r"""<div class="victron-dash" style="font-family:system-ui,-apple-system,'Segoe UI',sans-serif;color:#e2e8f0;background:linear-gradient(155deg,#0f172a 0%,#134e4a 35%,#0f172a 70%,#1e1b4b 100%);border-radius:16px;padding:clamp(12px,2vw,20px);box-shadow:0 24px 48px -12px rgba(0,0,0,0.55),inset 0 1px 0 rgba(255,255,255,0.08);border:1px solid rgba(45,212,191,0.25);width:100%;box-sizing:border-box;">
  <div style="display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:space-between;margin-bottom:16px;">
    <div>
      <div style="font-size:0.75em;text-transform:uppercase;letter-spacing:0.12em;color:#5eead4;font-weight:600;">Victron Cerbo GX</div>
      <div style="font-size:1.35em;font-weight:700;color:#f8fafc;margin-top:4px;">Energy Overview</div>
    </div>
    <div style="display:flex;flex-wrap:wrap;gap:10px;align-items:center;">
      <div :style="inverterBadgeStyle" style="padding:10px 18px;border-radius:999px;font-weight:700;font-size:0.95em;text-transform:uppercase;letter-spacing:0.04em;">{{ inverterState }}</div>
      <div v-if="gridLost" style="padding:8px 14px;border-radius:8px;background:rgba(239,68,68,0.2);border:1px solid #ef4444;color:#fecaca;font-weight:600;font-size:0.85em;">Grid Lost</div>
      <div style="padding:8px 14px;border-radius:8px;background:rgba(255,255,255,0.06);color:#94a3b8;font-size:0.85em;display:flex;align-items:baseline;gap:6px;">
        <span>Updated</span>
        <span style="font-variant-numeric:tabular-nums;font-weight:700;color:#e2e8f0;letter-spacing:0.04em;">{{ updateElapsed }}</span>
        <span style="font-size:0.85em;opacity:0.75;">ago</span>
      </div>
    </div>
  </div>

  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin-bottom:16px;">
    <div :style="cardStyle('#14b8a6')" style="border-radius:14px;padding:16px;text-align:center;">
      <div style="font-size:0.75em;color:#99f6e4;text-transform:uppercase;letter-spacing:0.08em;">Battery SoC</div>
      <div style="font-size:2.4em;font-weight:800;line-height:1.1;margin:8px 0;color:#fff;">{{ socDisplay }}</div>
      <div style="font-size:0.85em;color:#cbd5e1;">{{ batteryVoltage }} · {{ formatBatteryPower(batteryPower) }}</div>
    </div>
    <div :style="cardStyle('#3b82f6')" style="border-radius:14px;padding:16px;">
      <div style="font-size:0.75em;color:#93c5fd;text-transform:uppercase;letter-spacing:0.08em;">Grid L1</div>
      <div :style="{ color: signedColor(gridPower), fontSize: '1.8em', fontWeight: 800, margin: '8px 0' }">{{ formatGridPower(gridPower) }}</div>
      <div style="font-size:0.8em;color:#94a3b8;">{{ gridHint }}</div>
    </div>
    <div :style="cardStyle('#f59e0b')" style="border-radius:14px;padding:16px;">
      <div style="font-size:0.75em;color:#fde68a;text-transform:uppercase;letter-spacing:0.08em;">Consumption L1</div>
      <div style="font-size:1.8em;font-weight:800;margin:8px 0;color:#fff;">{{ formatW(loadConsumption) }}</div>
      <div style="font-size:0.8em;color:#94a3b8;">AC load</div>
    </div>
    <div :style="cardStyle('#eab308')" style="border-radius:14px;padding:16px;">
      <div style="font-size:0.75em;color:#fef08a;text-transform:uppercase;letter-spacing:0.08em;">PV (AC output)</div>
      <div style="font-size:1.8em;font-weight:800;margin:8px 0;color:#fff;">{{ formatW(pvAcOutput) }}</div>
      <div style="font-size:0.8em;color:#94a3b8;">DC {{ formatW(pvDcPower) }} · {{ pvDcCurrent }}</div>
    </div>
  </div>

  <div v-if="automation" style="margin-bottom:16px;padding:14px 16px;border-radius:12px;border:1px solid rgba(255,255,255,0.12);" :style="{ background: automation.can_add_load ? 'linear-gradient(90deg,rgba(16,185,129,0.18),rgba(6,95,70,0.08))' : 'linear-gradient(90deg,rgba(239,68,68,0.15),rgba(127,29,29,0.08))' }">
    <div style="display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:space-between;">
      <div>
        <div style="font-size:0.75em;text-transform:uppercase;letter-spacing:0.1em;color:#cbd5e1;">Load automation · PV − consumption</div>
        <div style="font-size:1.5em;font-weight:800;margin-top:4px;" :style="{ color: signedColor(automation.headroom_w) }">{{ formatHeadroom(automation.headroom_w) }}</div>
        <div style="font-size:0.8em;color:#94a3b8;margin-top:4px;">PV {{ formatW(automation.pv_power_w) }} − load {{ formatW(automation.consumption_l1_w) }}</div>
      </div>
      <div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;">
        <button @click="startDiscretionary" :disabled="!automation.can_add_load" :style="startBtnStyle">Start discretionary</button>
        <button @click="stopDiscretionary" style="padding:10px 16px;border:none;border-radius:10px;font-weight:700;cursor:pointer;background:linear-gradient(135deg,#ef4444,#dc2626);color:#fff;">Stop discretionary</button>
        <span :style="discBadgeStyle">{{ discretionaryLabel }}</span>
      </div>
    </div>
  </div>

  <div v-if="forecastSolar" style="margin-bottom:16px;padding:14px;border-radius:12px;background:rgba(255,255,255,0.04);border:1px solid rgba(250,204,21,0.25);">
    <div style="display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between;margin-bottom:10px;">
      <div style="font-weight:600;color:#fde047;">Solar forecast · {{ forecastSolar.location || 'Lunca Cetătuui' }}</div>
      <div style="font-size:0.8em;color:#94a3b8;">Open-Meteo · {{ forecastSolar.time || '—' }}</div>
    </div>
    <div style="display:flex;flex-wrap:wrap;gap:16px;font-size:0.9em;">
      <span>Now: <strong>{{ forecastRadiation }}</strong></span>
      <span>Today: <strong>{{ forecastToday }}</strong></span>
      <span>{{ forecastSolar.is_day ? 'Daylight' : 'Night' }}</span>
    </div>
  </div>

  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px;">
    <div style="background:rgba(255,255,255,0.04);border-radius:12px;padding:14px;border:1px solid rgba(255,255,255,0.08);">
      <div style="font-weight:600;color:#a5f3fc;margin-bottom:10px;">Battery</div>
      <div style="display:grid;gap:8px;font-size:0.9em;">
        <div style="display:flex;justify-content:space-between;"><span style="color:#94a3b8;">Voltage</span><span>{{ batteryVoltage }}</span></div>
        <div style="display:flex;justify-content:space-between;"><span style="color:#94a3b8;">Power</span><span :style="{ color: signedColor(batteryPower) }">{{ formatBatteryPower(batteryPower) }}</span></div>
      </div>
    </div>
    <div style="background:rgba(255,255,255,0.04);border-radius:12px;padding:14px;border:1px solid rgba(255,255,255,0.08);">
      <div style="font-weight:600;color:#93c5fd;margin-bottom:10px;">Load & VE.Bus</div>
      <div style="display:grid;gap:8px;font-size:0.9em;">
        <div style="display:flex;justify-content:space-between;"><span style="color:#94a3b8;">Output L1</span><span>{{ formatW(loadOutput) }}</span></div>
        <div style="display:flex;justify-content:space-between;"><span style="color:#94a3b8;">Input L1</span><span>{{ formatW(loadInput) }}</span></div>
        <div style="display:flex;justify-content:space-between;"><span style="color:#94a3b8;">AC out</span><span>{{ formatW(inverterAcOut) }}</span></div>
      </div>
    </div>
    <div style="background:rgba(255,255,255,0.04);border-radius:12px;padding:14px;border:1px solid rgba(255,255,255,0.08);">
      <div style="font-weight:600;color:#c4b5fd;margin-bottom:10px;">Inverter</div>
      <div style="display:grid;gap:8px;font-size:0.9em;">
        <div style="display:flex;justify-content:space-between;"><span style="color:#94a3b8;">State</span><span>{{ inverterState }} ({{ inverterStateCode }})</span></div>
        <div style="display:flex;justify-content:space-between;"><span style="color:#94a3b8;">AC in</span><span>{{ inverterAcInV }} · {{ formatW(inverterAcInP) }}</span></div>
        <div style="display:flex;justify-content:space-between;"><span style="color:#94a3b8;">DC bus</span><span>{{ inverterDcV }}</span></div>
      </div>
    </div>
    <div style="background:rgba(255,255,255,0.04);border-radius:12px;padding:14px;border:1px solid rgba(255,255,255,0.08);">
      <div style="font-weight:600;color:#fde047;margin-bottom:10px;">Solar / PV</div>
      <div style="display:grid;gap:8px;font-size:0.9em;">
        <div style="display:flex;justify-content:space-between;"><span style="color:#94a3b8;">AC grid L1</span><span>{{ formatW(pvAcGrid) }}</span></div>
        <div style="display:flex;justify-content:space-between;"><span style="color:#94a3b8;">DC current</span><span>{{ pvDcCurrent }}</span></div>
      </div>
    </div>
  </div>

  <div v-if="weekChart.length" style="margin-top:16px;margin-bottom:8px;padding:14px;border-radius:14px;background:rgba(0,0,0,0.28);border:1px solid rgba(94,234,212,0.2);">
    <div style="display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between;margin-bottom:10px;">
      <div style="font-weight:700;color:#5eead4;">7-day history (15 min buckets)</div>
      <div style="display:flex;flex-wrap:wrap;gap:10px;font-size:0.72em;color:#94a3b8;">
        <span v-for="s in chartLegend" :key="s.key"><span :style="{display:'inline-block',width:'8px',height:'8px',borderRadius:'50%',background:s.color,marginRight:'4px'}"></span>{{ s.label }}</span>
      </div>
    </div>
    <svg viewBox="0 0 800 260" style="width:100%;height:auto;display:block;">
      <line x1="10" y1="115" x2="790" y2="115" stroke="rgba(255,255,255,0.12)" stroke-width="1" stroke-dasharray="4 4"/>
      <g v-for="(tick,i) in chartXTicks" :key="'x'+i">
        <line :x1="tick.x" y1="12" :x2="tick.x" y2="218" stroke="rgba(255,255,255,0.08)" stroke-width="1"/>
        <text :x="tick.x" y="248" fill="#94a3b8" font-size="11" font-weight="600" text-anchor="middle">{{ tick.label }}</text>
      </g>
      <path v-for="line in chartLines" :key="line.key" :d="line.path" fill="none" :stroke="line.color" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>
    </svg>
    <div style="font-size:0.72em;color:#64748b;margin-top:6px;">Fixed 7-day window · center line = 0 W · SoC 0–100% · {{ weekChart.length }} samples</div>
  </div>

  <div v-if="!msg.payload?.timestamp" style="text-align:center;padding:32px;color:#64748b;">
    Waiting for <code style="color:#5eead4;">energy/victron/status</code>
  </div>
</div>

<script>
export default {
  data() { return { now: Date.now(), timer: null }; },
  mounted() { this.timer = setInterval(() => { this.now = Date.now(); }, 1000); },
  unmounted() { clearInterval(this.timer); },
  methods: {
    sendCmd(action) { this.send({ payload: { action, source: 'dashboard', timestamp: new Date().toISOString() } }); },
    startDiscretionary() { this.sendCmd('start'); },
    stopDiscretionary() { this.sendCmd('stop'); },
    cardStyle(accent) {
      return { background: 'linear-gradient(145deg,rgba(255,255,255,0.08),rgba(255,255,255,0.02))', border: '1px solid rgba(255,255,255,0.1)', boxShadow: '0 8px 24px -8px ' + accent + '44' };
    },
    pad2(n) { return String(n).padStart(2, '0'); },
    chartX(t) {
      const w = this.chartWindow;
      return 10 + ((t - w.t0) / w.span) * 780;
    },
    formatW(val) {
      if (val == null || val === '') return '—';
      const n = Number(val);
      return Number.isNaN(n) ? String(val) : Math.round(n) + ' W';
    },
    formatBatteryPower(val) {
      if (val == null) return '—';
      const n = Number(val);
      if (Number.isNaN(n)) return String(val);
      const abs = Math.abs(Math.round(n));
      if (n > 0) return abs + ' W charging';
      if (n < 0) return abs + ' W discharging';
      return '0 W';
    },
    formatGridPower(val) {
      if (val == null) return '—';
      const n = Number(val);
      return Number.isNaN(n) ? String(val) : Math.abs(Math.round(n)) + ' W';
    },
    signedColor(val) {
      const n = Number(val);
      if (Number.isNaN(n) || n === 0) return '#e2e8f0';
      return n > 0 ? '#4ade80' : '#f87171';
    },
    formatHeadroom(val) {
      if (val == null) return '—';
      const n = Number(val);
      if (Number.isNaN(n)) return String(val);
      const abs = Math.abs(Math.round(n));
      if (n > 0) return '+' + abs + ' W surplus';
      if (n < 0) return '-' + abs + ' W deficit';
      return '0 W balanced';
    }
  },
  computed: {
    p() { return this.msg.payload || {}; },
    updateElapsed() {
      const ms = this.msg.metadata?.lastReportedMs;
      if (!ms) return '—:—:—';
      void this.now;
      const sec = Math.max(0, Math.floor((this.now - ms) / 1000));
      const h = Math.floor(sec / 3600);
      const m = Math.floor((sec % 3600) / 60);
      const s = sec % 60;
      if (h > 0) return this.pad2(h) + ':' + this.pad2(m) + ':' + this.pad2(s);
      return this.pad2(m) + ':' + this.pad2(s);
    },
    automation() { return this.p.automation || null; },
    weekChart() { return this.p.week_chart || []; },
    chartWindow() {
      void this.now;
      const WEEK = 7 * 86400000;
      const t1 = this.now;
      return { t0: t1 - WEEK, t1, span: WEEK };
    },
    discretionaryLoad() { return this.p.discretionary_load || { enabled: false }; },
    discretionaryLabel() { return this.discretionaryLoad.enabled ? 'Discretionary ON' : 'Discretionary OFF'; },
    startBtnStyle() {
      const ok = this.automation && this.automation.can_add_load;
      return { padding: '10px 16px', border: 'none', borderRadius: '10px', fontWeight: '700', cursor: ok ? 'pointer' : 'not-allowed', background: 'linear-gradient(135deg,#10b981,#059669)', color: '#fff', opacity: ok ? 1 : 0.45 };
    },
    discBadgeStyle() {
      const on = this.discretionaryLoad.enabled;
      return { padding: '8px 12px', borderRadius: '8px', fontSize: '0.85em', fontWeight: '600', background: on ? 'rgba(16,185,129,0.25)' : 'rgba(100,116,139,0.25)', color: on ? '#6ee7b7' : '#94a3b8' };
    },
    chartLegend() {
      return [
        { key: 'pv', label: 'PV', color: '#eab308' },
        { key: 'load', label: 'Load', color: '#f97316' },
        { key: 'grid', label: 'Grid', color: '#60a5fa' },
        { key: 'headroom', label: 'Headroom', color: '#34d399' },
        { key: 'invOut', label: 'Inv out', color: '#a78bfa' },
        { key: 'soc', label: 'SoC %', color: '#2dd4bf' }
      ];
    },
    chartPowerMax() {
      let m = 500;
      this.weekChart.forEach(p => {
        ['pv', 'load', 'grid', 'headroom', 'invOut', 'invIn', 'battP'].forEach(k => {
          const v = Math.abs(Number(p[k]) || 0);
          if (v > m) m = v;
        });
      });
      return Math.ceil(m / 500) * 500;
    },
    chartLines() {
      const pts = this.weekChart;
      if (!pts.length) return [];
      const w = this.chartWindow;
      const pmax = this.chartPowerMax;
      const specs = [
        { key: 'pv', color: '#eab308', kind: 'power' },
        { key: 'load', color: '#f97316', kind: 'power' },
        { key: 'grid', color: '#60a5fa', kind: 'power' },
        { key: 'headroom', color: '#34d399', kind: 'power' },
        { key: 'invOut', color: '#a78bfa', kind: 'power' },
        { key: 'soc', color: '#2dd4bf', kind: 'soc' }
      ];
      return specs.map(s => {
        let d = '';
        pts.forEach(p => {
          if (p.t < w.t0 || p.t > w.t1) return;
          const v = Number(p[s.key]);
          if (Number.isNaN(v)) return;
          const x = this.chartX(p.t);
          const y = s.kind === 'soc' ? 218 - (v / 100) * 206 : 115 - (v / pmax) * 100;
          d += (d ? ' L' : 'M') + x.toFixed(1) + ',' + y.toFixed(1);
        });
        return { key: s.key, color: s.color, path: d };
      }).filter(l => l.path);
    },
    chartXTicks() {
      void this.now;
      const w = this.chartWindow;
      const ticks = [];
      const d = new Date(w.t0);
      d.setHours(0, 0, 0, 0);
      while (d.getTime() <= w.t1) {
        const t = d.getTime();
        if (t >= w.t0) {
          ticks.push({
            x: this.chartX(t),
            label: d.toLocaleDateString(undefined, { weekday: 'short', day: 'numeric' })
          });
        }
        d.setDate(d.getDate() + 1);
      }
      return ticks;
    },
    inverterState() { return this.p.inverter?.state || 'Unknown'; },
    inverterStateCode() { return this.p.inverter?.state_code ?? '—'; },
    gridLost() { return this.p.inverter?.grid_lost === true; },
    socDisplay() { const v = this.p.battery?.soc_pct; return v != null ? v + '%' : '—'; },
    batteryVoltage() { const v = this.p.battery?.voltage_v; return v != null ? v + ' V' : '—'; },
    batteryPower() { return this.p.battery?.power_w; },
    gridPower() { return this.p.grid?.power_l1_w; },
    gridHint() {
      const n = Number(this.gridPower);
      if (Number.isNaN(n)) return '—';
      if (n > 0) return 'Importing from grid';
      if (n < 0) return 'Exporting to grid';
      return 'Neutral';
    },
    loadConsumption() { return this.p.load?.consumption_l1_w; },
    loadOutput() { return this.p.load?.output_l1_w; },
    loadInput() { return this.p.load?.input_l1_w; },
    pvAcOutput() { return this.p.pv?.ac_output_l1_w; },
    pvAcGrid() { return this.p.pv?.ac_grid_l1_w; },
    pvDcPower() { return this.p.pv?.dc_power_w; },
    pvDcCurrent() { const v = this.p.pv?.dc_current_a; return v != null ? v + ' A' : '—'; },
    inverterAcInV() { const v = this.p.inverter?.ac_in_voltage_l1_v; return v != null ? v + ' V' : '—'; },
    inverterAcInP() { return this.p.inverter?.ac_in_power_l1_w; },
    inverterAcOut() { return this.p.inverter?.ac_out_power_l1_w; },
    inverterDcV() { const v = this.p.inverter?.dc_voltage_v; return v != null ? v + ' V' : '—'; },
    forecastSolar() { return this.p.forecast_solar || null; },
    forecastRadiation() { const v = this.forecastSolar?.shortwave_radiation_wm2; return v != null ? Math.round(v) + ' W/m²' : '—'; },
    forecastToday() {
      const days = this.p.forecast_daily?.days;
      if (days && days[0] && days[0].shortwave_radiation_sum_kwh_m2 != null) return days[0].shortwave_radiation_sum_kwh_m2 + ' kWh/m²';
      return '—';
    },
    inverterBadgeStyle() {
      const s = (this.inverterState || '').toLowerCase();
      let bg = 'linear-gradient(135deg,#64748b,#475569)';
      if (s === 'passthru' || s === 'float' || s === 'storage') bg = 'linear-gradient(135deg,#10b981,#059669)';
      else if (s === 'inverting' || s === 'bulk' || s === 'absorption') bg = 'linear-gradient(135deg,#3b82f6,#2563eb)';
      else if (s === 'fault' || s === 'off') bg = 'linear-gradient(135deg,#ef4444,#dc2626)';
      return { background: bg, color: '#fff', boxShadow: '0 4px 16px rgba(0,0,0,0.3)' };
    }
  }
};
</script>"""

flow = [
    {
        "id": "victron_energy_comment",
        "type": "comment",
        "z": "tab_dashboard",
        "name": "═══════════════ VICTRON ENERGY STATUS DASHBOARD ═══════════════",
        "info": "## Victron Energy Status Dashboard\n\n**Flow 811** — live metrics, 7-day chart, discretionary load commands.\n\n### MQTT subscribe\n- `energy/victron/status`\n- `energy/victron/forecast/solar/current`\n- `energy/victron/forecast/solar/daily`\n\n### MQTT publish (dashboard buttons)\n- `energy/victron/command/discretionary/start`\n- `energy/victron/command/discretionary/stop`\n- `energy/victron/automation/discretionary_load/state` (retained)\n\nSee [docs/ENERGY_NODE_RED.md](../../docs/ENERGY_NODE_RED.md).",
        "x": 320,
        "y": 40,
        "wires": [],
    },
    {
        "id": "mqtt_in_victron_status",
        "type": "mqtt in",
        "z": "tab_dashboard",
        "name": "Victron Status",
        "topic": "energy/victron/status",
        "qos": "1",
        "datatype": "json",
        "broker": "mqtt_broker_local",
        "nl": False,
        "rap": True,
        "rh": 0,
        "inputs": 0,
        "x": 180,
        "y": 140,
        "wires": [["func_victron_process_status"]],
    },
    {
        "id": "func_victron_process_status",
        "type": "function",
        "z": "tab_dashboard",
        "name": "Process Victron Status",
        "func": PROCESS_FUNC,
        "outputs": 1,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": 430,
        "y": 140,
        "wires": [["template_victron_energy_dashboard"]],
    },
    {
        "id": "mqtt_in_victron_forecast",
        "type": "mqtt in",
        "z": "tab_dashboard",
        "name": "Solar Forecast Current",
        "topic": "energy/victron/forecast/solar/current",
        "qos": "1",
        "datatype": "json",
        "broker": "mqtt_broker_local",
        "nl": False,
        "rap": True,
        "rh": 0,
        "inputs": 0,
        "x": 200,
        "y": 220,
        "wires": [["func_victron_store_forecast"]],
    },
    {
        "id": "func_victron_store_forecast",
        "type": "function",
        "z": "tab_dashboard",
        "name": "Store Solar Forecast",
        "func": "if (!msg.payload || typeof msg.payload !== 'object') return null;\nflow.set('victron_solar_forecast', msg.payload);\nconst last = flow.get('last_victron_status');\nif (!last) return null;\nconst meta = flow.get('victron_energy_metadata') || {};\nconst daily = flow.get('victron_solar_forecast_daily');\nreturn { payload: { ...last, forecast_solar: msg.payload, forecast_daily: daily || null, week_chart: flow.get('victron_week_history') || [], discretionary_load: flow.get('victron_discretionary_load') || { enabled: false } }, metadata: meta };",
        "outputs": 1,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": 450,
        "y": 220,
        "wires": [["template_victron_energy_dashboard"]],
    },
    {
        "id": "mqtt_in_victron_forecast_daily",
        "type": "mqtt in",
        "z": "tab_dashboard",
        "name": "Solar Forecast Daily",
        "topic": "energy/victron/forecast/solar/daily",
        "qos": "1",
        "datatype": "json",
        "broker": "mqtt_broker_local",
        "nl": False,
        "rap": True,
        "rh": 0,
        "inputs": 0,
        "x": 200,
        "y": 280,
        "wires": [["func_victron_store_forecast_daily"]],
    },
    {
        "id": "func_victron_store_forecast_daily",
        "type": "function",
        "z": "tab_dashboard",
        "name": "Store Daily Forecast",
        "func": "if (!msg.payload || typeof msg.payload !== 'object') return null;\nflow.set('victron_solar_forecast_daily', msg.payload);\nconst last = flow.get('last_victron_status');\nif (!last) return null;\nconst meta = flow.get('victron_energy_metadata') || {};\nconst current = flow.get('victron_solar_forecast');\nreturn { payload: { ...last, forecast_solar: current || null, forecast_daily: msg.payload, week_chart: flow.get('victron_week_history') || [], discretionary_load: flow.get('victron_discretionary_load') || { enabled: false } }, metadata: meta };",
        "outputs": 1,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": 450,
        "y": 280,
        "wires": [["template_victron_energy_dashboard"]],
    },
    {
        "id": "inject_victron_refresh",
        "type": "inject",
        "z": "tab_dashboard",
        "name": "Refresh dashboard",
        "props": [{"p": "payload"}],
        "repeat": "60",
        "crontab": "",
        "once": True,
        "onceDelay": 2,
        "topic": "",
        "payload": "",
        "payloadType": "date",
        "x": 190,
        "y": 360,
        "wires": [["func_victron_refresh_dashboard"]],
    },
    {
        "id": "func_victron_refresh_dashboard",
        "type": "function",
        "z": "tab_dashboard",
        "name": "Refresh dashboard state",
        "func": REFRESH_FUNC,
        "outputs": 1,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": 440,
        "y": 360,
        "wires": [["template_victron_energy_dashboard"]],
    },
    {
        "id": "template_victron_energy_dashboard",
        "type": "ui-template",
        "z": "tab_dashboard",
        "group": "ui_group_victron_energy",
        "name": "Victron Energy Dashboard",
        "order": 1,
        "width": 0,
        "height": 0,
        "format": TEMPLATE.replace("\n", "\\n"),
        "storeOutMessages": True,
        "fwdInMessages": True,
        "resendOnRefresh": True,
        "templateScope": "local",
        "className": "",
        "x": 720,
        "y": 200,
        "wires": [["func_victron_discretionary_cmd"]],
    },
    {
        "id": "func_victron_discretionary_cmd",
        "type": "function",
        "z": "tab_dashboard",
        "name": "Discretionary load command",
        "func": DISC_FUNC,
        "outputs": 3,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": 980,
        "y": 200,
        "wires": [
            ["mqtt_out_victron_disc_cmd"],
            ["mqtt_out_victron_disc_state"],
            ["template_victron_energy_dashboard"],
        ],
    },
    {
        "id": "mqtt_out_victron_disc_cmd",
        "type": "mqtt out",
        "z": "tab_dashboard",
        "name": "Discretionary command",
        "topic": "",
        "qos": "1",
        "retain": "false",
        "respTopic": "",
        "contentType": "application/json",
        "userProps": "",
        "correl": "",
        "expiry": "",
        "broker": "mqtt_broker_local",
        "x": 1230,
        "y": 180,
        "wires": [],
    },
    {
        "id": "mqtt_out_victron_disc_state",
        "type": "mqtt out",
        "z": "tab_dashboard",
        "name": "Discretionary state",
        "topic": "energy/victron/automation/discretionary_load/state",
        "qos": "1",
        "retain": "true",
        "respTopic": "",
        "contentType": "application/json",
        "userProps": "",
        "correl": "",
        "expiry": "",
        "broker": "mqtt_broker_local",
        "x": 1240,
        "y": 240,
        "wires": [],
    },
]

# Fix format: escape for JSON (newlines in template)
for node in flow:
    if node.get("id") == "template_victron_energy_dashboard":
        node["format"] = TEMPLATE

OUT.write_text(json.dumps(flow, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")
print("Wrote", OUT)
