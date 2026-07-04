#!/usr/bin/env python3
"""Generate 821-huawei-energy-status.json for Node-RED Dashboard 2.0."""

from __future__ import annotations

import json
from pathlib import Path

DASHBOARD_HTML = r"""<div class="huawei-dash" style="font-family:system-ui,-apple-system,'Segoe UI',sans-serif;color:#e2e8f0;background:linear-gradient(155deg,#0f172a 0%,#7c2d12 25%,#0f172a 65%,#1e1b4b 100%);border-radius:16px;padding:clamp(12px,2vw,20px);box-shadow:0 24px 48px -12px rgba(0,0,0,0.55);border:1px solid rgba(251,146,60,0.3);width:100%;box-sizing:border-box;">
  <div style="display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:space-between;margin-bottom:16px;">
    <div>
      <div style="font-size:0.75em;text-transform:uppercase;letter-spacing:0.12em;color:#fb923c;font-weight:600;">Huawei SUN2000</div>
      <div style="font-size:1.35em;font-weight:700;color:#f8fafc;margin-top:4px;">{{ deviceModel }}</div>
      <div style="font-size:0.85em;color:#94a3b8;margin-top:4px;">S/N {{ deviceSerial }}</div>
    </div>
    <div style="padding:8px 14px;border-radius:8px;background:rgba(255,255,255,0.06);color:#94a3b8;font-size:0.85em;">
      Updated <span style="font-variant-numeric:tabular-nums;font-weight:700;color:#e2e8f0;">{{ updateElapsed }}</span> ago
    </div>
  </div>
  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:16px;">
    <div style="border-radius:14px;padding:16px;text-align:center;background:linear-gradient(145deg,rgba(251,146,60,0.2),rgba(0,0,0,0.2));border:1px solid rgba(251,146,60,0.35);">
      <div style="font-size:0.75em;color:#fdba74;text-transform:uppercase;">Active power</div>
      <div style="font-size:2.2em;font-weight:800;margin:8px 0;color:#fff;">{{ formatW(activePower) }}</div>
    </div>
    <div style="border-radius:14px;padding:16px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);">
      <div style="font-size:0.75em;color:#fde68a;text-transform:uppercase;">Daily yield</div>
      <div style="font-size:1.8em;font-weight:800;margin:8px 0;">{{ dailyYield }}</div>
    </div>
    <div style="border-radius:14px;padding:16px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);">
      <div style="font-size:0.75em;color:#93c5fd;text-transform:uppercase;">DC input</div>
      <div style="font-size:1.8em;font-weight:800;margin:8px 0;">{{ formatW(dcInput) }}</div>
    </div>
    <div style="border-radius:14px;padding:16px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);">
      <div style="font-size:0.75em;color:#a5f3fc;text-transform:uppercase;">Grid frequency</div>
      <div style="font-size:1.8em;font-weight:800;margin:8px 0;">{{ gridHz }}</div>
    </div>
  </div>
  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-bottom:16px;">
    <div style="background:rgba(255,255,255,0.04);border-radius:12px;padding:14px;border:1px solid rgba(255,255,255,0.08);">
      <div style="font-weight:600;color:#fdba74;margin-bottom:8px;">PV string 1</div>
      <div>{{ pv1Voltage }} · {{ pv1Current }}</div>
    </div>
    <div style="background:rgba(255,255,255,0.04);border-radius:12px;padding:14px;border:1px solid rgba(255,255,255,0.08);">
      <div style="font-weight:600;color:#fdba74;margin-bottom:8px;">PV string 2</div>
      <div>{{ pv2Voltage }} · {{ pv2Current }}</div>
    </div>
    <div style="background:rgba(255,255,255,0.04);border-radius:12px;padding:14px;border:1px solid rgba(255,255,255,0.08);">
      <div style="font-weight:600;color:#c4b5fd;margin-bottom:8px;">Rated power</div>
      <div>{{ ratedPower }}</div>
    </div>
  </div>
  <div v-if="weekChart.length" style="margin-top:8px;padding:14px;border-radius:14px;background:rgba(0,0,0,0.28);border:1px solid rgba(251,146,60,0.25);">
    <div style="font-weight:700;color:#fb923c;margin-bottom:10px;">7-day active power (15 min buckets)</div>
    <svg viewBox="0 0 800 200" style="width:100%;height:auto;display:block;">
      <line x1="10" y1="100" x2="790" y2="100" stroke="rgba(255,255,255,0.12)" stroke-width="1" stroke-dasharray="4 4"/>
      <g v-for="(tick,i) in chartXTicks" :key="'x'+i">
        <line :x1="tick.x" y1="12" :x2="tick.x" y2="180" stroke="rgba(255,255,255,0.08)" stroke-width="1"/>
        <text :x="tick.x" y="196" fill="#94a3b8" font-size="11" text-anchor="middle">{{ tick.label }}</text>
      </g>
      <path :d="powerPath" fill="none" stroke="#fb923c" stroke-width="2.5" stroke-linejoin="round"/>
    </svg>
  </div>
  <div v-if="!msg.payload?.timestamp" style="text-align:center;padding:32px;color:#64748b;">
    Waiting for <code style="color:#fb923c;">energy/huawei/status</code>
  </div>
</div>

<script>
export default {
  data() { return { now: Date.now(), timer: null }; },
  mounted() { this.timer = setInterval(() => { this.now = Date.now(); }, 1000); },
  unmounted() { clearInterval(this.timer); },
  methods: {
    pad2(n) { return String(n).padStart(2, '0'); },
    chartX(t) {
      const w = this.chartWindow;
      return 10 + ((t - w.t0) / w.span) * 780;
    },
    formatW(val) {
      if (val == null || val === '') return '—';
      const n = Number(val);
      return Number.isNaN(n) ? String(val) : Math.round(n) + ' W';
    }
  },
  computed: {
    p() { return this.msg.payload || {}; },
    updateElapsed() {
      const ms = this.msg.metadata?.lastReportedMs;
      if (!ms) return '—:—';
      void this.now;
      const sec = Math.max(0, Math.floor((this.now - ms) / 1000));
      const m = Math.floor(sec / 60);
      const s = sec % 60;
      return this.pad2(m) + ':' + this.pad2(s);
    },
    deviceModel() { return this.p.device?.model || 'SUN2000'; },
    deviceSerial() { return this.p.device?.serial || '—'; },
    activePower() { return this.p.inverter?.active_power_w; },
    dcInput() { return this.p.pv?.input_power_w; },
    dailyYield() {
      const v = this.p.inverter?.daily_yield_kwh;
      return v != null ? Number(v).toFixed(2) + ' kWh' : '—';
    },
    gridHz() {
      const v = this.p.inverter?.grid_frequency_hz;
      return v != null ? Number(v).toFixed(2) + ' Hz' : '—';
    },
    pv1Voltage() { const v = this.p.pv?.string1_voltage_v; return v != null ? v + ' V' : '—'; },
    pv1Current() { const v = this.p.pv?.string1_current_a; return v != null ? v + ' A' : '—'; },
    pv2Voltage() { const v = this.p.pv?.string2_voltage_v; return v != null ? v + ' V' : '—'; },
    pv2Current() { const v = this.p.pv?.string2_current_a; return v != null ? v + ' A' : '—'; },
    ratedPower() {
      const v = this.p.device?.rated_power_w;
      return v != null ? Math.round(v) + ' W' : '—';
    },
    weekChart() { return this.p.week_chart || []; },
    chartWindow() {
      void this.now;
      const WEEK = 7 * 86400000;
      const t1 = this.now;
      return { t0: t1 - WEEK, t1, span: WEEK };
    },
    chartPowerMax() {
      let m = 500;
      this.weekChart.forEach(p => {
        const v = Math.abs(Number(p.active) || 0);
        if (v > m) m = v;
      });
      return Math.ceil(m / 500) * 500;
    },
    powerPath() {
      const pts = this.weekChart;
      if (!pts.length) return '';
      const w = this.chartWindow;
      const pmax = this.chartPowerMax;
      let d = '';
      pts.forEach(p => {
        if (p.t < w.t0 || p.t > w.t1) return;
        const v = Number(p.active);
        if (Number.isNaN(v)) return;
        const x = this.chartX(p.t);
        const y = 100 - (v / pmax) * 88;
        d += (d ? ' L' : 'M') + x.toFixed(1) + ',' + y.toFixed(1);
      });
      return d;
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
    }
  }
};
</script>"""

PROCESS_STATUS = r"""const data = msg.payload;
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
node.status({ fill: 'green', shape: 'dot', text: `PV ${ap != null ? ap : '?'} W` });
return msg;"""

REFRESH = r"""const last = flow.get('last_huawei_status');
if (!last) return null;
return {
    payload: { ...last, week_chart: flow.get('huawei_week_history') || [] },
    metadata: flow.get('huawei_energy_metadata') || {}
};"""


def node(**kwargs):
    return kwargs


flow = [
    node(
        id="huawei_energy_comment",
        type="comment",
        z="tab_dashboard",
        name="═══════════════ HUAWEI ENERGY STATUS DASHBOARD ═══════════════",
        info="## Huawei Energy Status Dashboard\n\n**Flow 821** — SUN2000 live metrics and 7-day chart.\n\nMQTT: `energy/huawei/status`\nGlobal: `huawei_energy_state`",
        x=320,
        y=520,
        wires=[],
    ),
    node(
        id="mqtt_in_huawei_status",
        type="mqtt in",
        z="tab_dashboard",
        name="Huawei Status",
        topic="energy/huawei/status",
        qos="1",
        datatype="json",
        broker="mqtt_broker_local",
        nl=False,
        rap=True,
        rh=0,
        inputs=0,
        x=180,
        y=620,
        wires=[["func_huawei_process_status"]],
    ),
    node(
        id="func_huawei_process_status",
        type="function",
        z="tab_dashboard",
        name="Process Huawei Status",
        func=PROCESS_STATUS,
        outputs=1,
        noerr=0,
        initialize="",
        finalize="",
        libs=[],
        x=430,
        y=620,
        wires=[["template_huawei_energy_dashboard"]],
    ),
    node(
        id="inject_huawei_refresh",
        type="inject",
        z="tab_dashboard",
        name="Refresh dashboard",
        props=[{"p": "payload"}],
        repeat="60",
        crontab="",
        once=True,
        onceDelay=2,
        topic="",
        payload="",
        payloadType="date",
        x=190,
        y=700,
        wires=[["func_huawei_refresh_dashboard"]],
    ),
    node(
        id="func_huawei_refresh_dashboard",
        type="function",
        z="tab_dashboard",
        name="Refresh dashboard state",
        func=REFRESH,
        outputs=1,
        noerr=0,
        initialize="",
        finalize="",
        libs=[],
        x=440,
        y=700,
        wires=[["template_huawei_energy_dashboard"]],
    ),
    node(
        id="template_huawei_energy_dashboard",
        type="ui-template",
        z="tab_dashboard",
        group="ui_group_huawei_energy",
        name="Huawei Energy Dashboard",
        order=1,
        width=0,
        height=0,
        format=DASHBOARD_HTML,
        storeOutMessages=True,
        fwdInMessages=True,
        resendOnRefresh=True,
        templateScope="local",
        className="",
        x=720,
        y=660,
        wires=[[]],
    ),
]

out = Path(__file__).resolve().parent / "821-huawei-energy-status.json"
out.write_text(json.dumps(flow, indent=4) + "\n", encoding="utf-8")
print(f"Wrote {out}")
