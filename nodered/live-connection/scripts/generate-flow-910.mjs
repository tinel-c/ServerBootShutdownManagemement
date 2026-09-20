/**
 * Generate flow 910 — Automation host metrics dashboard (CPU / memory / disk).
 * Charts: last 1 hour, last 25 hours, last month.
 *
 *   node nodered/live-connection/scripts/generate-flow-910.mjs
 *   node nodered/live-connection/scripts/deploy-flow-910.mjs
 */
import { writeFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const outFile = join(
  dirname(fileURLToPath(import.meta.url)),
  "..",
  "..",
  "flows",
  "910-host-metrics-dashboard.json"
);

const PROCESS_FUNC = `let data = msg.payload;
if (typeof data === 'string') {
    try { data = JSON.parse(data); } catch (e) { return null; }
}
if (!data || typeof data !== 'object' || !data.timestamp) {
    node.warn('Invalid host metrics payload');
    return null;
}

const receivedMs = Date.now();
let reportMs;
try { reportMs = new Date(data.timestamp).getTime(); } catch (e) { reportMs = receivedMs; }
if (!Number.isFinite(reportMs)) reportMs = receivedMs;

const point = {
    t: reportMs,
    cpu: data.cpu?.percent ?? null,
    mem: data.memory?.percent ?? null,
    root: data.disk?.root?.percent ?? null,
    dataDisk: data.disk?.data?.percent ?? null,
    load1: data.load?.['1'] ?? null
};

const FINE_MS = 60 * 1000;
const HOUR_MS = 60 * 60 * 1000;
const DAY25_MS = 25 * HOUR_MS;
const MONTH_MS = 31 * 24 * HOUR_MS;

function upsert(hist, bucketMs, keepMs) {
    const bucket = Math.floor(reportMs / bucketMs) * bucketMs;
    if (hist.length && hist[hist.length - 1].bucket === bucket) {
        hist[hist.length - 1] = { bucket, ...point };
    } else {
        hist.push({ bucket, ...point });
    }
    const cutoff = Date.now() - keepMs;
    return hist.filter(h => h.t >= cutoff);
}

let fine = flow.get('host_fine_history') || [];
fine = upsert(fine, FINE_MS, DAY25_MS);
flow.set('host_fine_history', fine);

let month = flow.get('host_month_history') || [];
month = upsert(month, HOUR_MS, MONTH_MS);
flow.set('host_month_history', month);

flow.set('last_host_metrics', data);
data.fine_chart = fine;
data.month_chart = month;
data.receivedAtMs = receivedMs;

return { payload: data };`;

const REFRESH_FUNC = `const last = flow.get('last_host_metrics');
if (!last) return null;
return {
    payload: {
        ...last,
        fine_chart: flow.get('host_fine_history') || [],
        month_chart: flow.get('host_month_history') || []
    }
};`;

const TEMPLATE = `<div class="hm-dash" style="font-family:'DM Sans',system-ui,-apple-system,'Segoe UI',sans-serif;color:#e7e5e4;background:
  radial-gradient(1200px 500px at 10% -10%, rgba(245,158,11,0.18), transparent 55%),
  radial-gradient(900px 420px at 100% 0%, rgba(14,165,233,0.16), transparent 50%),
  linear-gradient(165deg,#0c0a09 0%,#1c1917 42%,#0f172a 100%);
  border-radius:18px;padding:clamp(14px,2vw,22px);border:1px solid rgba(245,158,11,0.22);
  box-shadow:0 28px 50px -18px rgba(0,0,0,0.65), inset 0 1px 0 rgba(255,255,255,0.06);
  width:100%;box-sizing:border-box;">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@500;700&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">

  <div style="display:flex;flex-wrap:wrap;gap:12px;align-items:flex-end;justify-content:space-between;margin-bottom:18px;">
    <div>
      <div style="font-size:0.72rem;letter-spacing:0.16em;text-transform:uppercase;color:#fbbf24;font-weight:700;">Automation host</div>
      <div style="font-size:1.45rem;font-weight:700;color:#fafaf9;margin-top:4px;font-family:'DM Sans',sans-serif;">{{ hostName }}</div>
      <div style="font-size:0.78rem;color:#a8a29e;margin-top:4px;font-family:'JetBrains Mono',monospace;">{{ ageLabel }}</div>
    </div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;">
      <button v-for="r in chartRanges" :key="r.key" type="button" @click="setChartRange(r.key)"
        :style="chartRangeBtnStyle(r.key)">{{ r.label }}</button>
    </div>
  </div>

  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin-bottom:18px;">
    <div v-for="g in gauges" :key="g.key" style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:12px 10px;text-align:center;">
      <svg viewBox="0 0 120 78" width="100%" style="max-width:160px;margin:0 auto;display:block;">
        <path d="M14 64 A46 46 0 0 1 106 64" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="10" stroke-linecap="round"/>
        <path :d="arcPath(g.value)" fill="none" :stroke="g.color" stroke-width="10" stroke-linecap="round"
          style="filter:drop-shadow(0 0 8px rgba(0,0,0,0.35)); transition: d 0.4s ease;"/>
        <text x="60" y="58" text-anchor="middle" fill="#fafaf9" font-size="18" font-weight="700" font-family="JetBrains Mono, monospace">{{ fmtPct(g.value) }}</text>
      </svg>
      <div style="font-size:0.72rem;letter-spacing:0.08em;text-transform:uppercase;color:#a8a29e;font-weight:700;margin-top:2px;">{{ g.label }}</div>
      <div style="font-size:0.7rem;color:#78716c;margin-top:4px;font-family:'JetBrains Mono',monospace;">{{ g.sub }}</div>
    </div>
  </div>

  <div style="background:rgba(0,0,0,0.28);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:12px 12px 8px;position:relative;">
    <div style="display:flex;flex-wrap:wrap;gap:14px;align-items:center;justify-content:space-between;margin-bottom:8px;">
      <div style="font-size:0.78rem;font-weight:700;color:#e7e5e4;">{{ chartTitle }}</div>
      <div style="display:flex;flex-wrap:wrap;gap:10px;font-size:0.68rem;font-family:'JetBrains Mono',monospace;">
        <span v-for="s in seriesMeta" :key="s.key" style="display:inline-flex;align-items:center;gap:6px;color:#a8a29e;">
          <span :style="{width:'10px',height:'10px',borderRadius:'999px',background:s.color,display:'inline-block'}"></span>{{ s.label }}
        </span>
      </div>
    </div>
    <svg :viewBox="'0 0 ' + cw + ' ' + ch" width="100%" style="display:block;height:auto;max-height:280px;touch-action:none;"
      @mousemove="onChartMove" @mouseleave="chartHover=null" @touchstart.prevent="onChartTouch" @touchmove.prevent="onChartTouch">
      <defs>
        <linearGradient id="hmGrid" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="rgba(255,255,255,0.06)"/>
          <stop offset="100%" stop-color="rgba(255,255,255,0)"/>
        </linearGradient>
      </defs>
      <rect x="0" y="0" :width="cw" :height="ch" fill="url(#hmGrid)" rx="8"/>
      <g v-for="y in yTicks" :key="'y'+y.v">
        <line :x1="padL" :x2="cw-padR" :y1="y.y" :y2="y.y" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>
        <text :x="padL-6" :y="y.y+3" text-anchor="end" fill="#78716c" font-size="10" font-family="JetBrains Mono, monospace">{{ y.v }}%</text>
      </g>
      <path v-for="s in seriesPaths" :key="s.key" :d="s.d" fill="none" :stroke="s.color" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round" opacity="0.95"/>
      <g v-if="chartHover">
        <line :x1="chartHover.x" :x2="chartHover.x" :y1="padT" :y2="ch-padB" stroke="rgba(251,191,36,0.45)" stroke-dasharray="4 4"/>
        <circle v-for="p in chartHover.points" :key="p.key" :cx="chartHover.x" :cy="p.y" r="3.5" :fill="p.color" stroke="#0c0a09" stroke-width="1.5"/>
      </g>
      <g v-for="x in xTicks" :key="'x'+x.t">
        <text :x="x.x" :y="ch-8" text-anchor="middle" fill="#78716c" font-size="10" font-family="JetBrains Mono, monospace">{{ x.label }}</text>
      </g>
    </svg>
    <div v-if="chartHover" style="position:absolute;pointer-events:none;z-index:2;min-width:140px;padding:8px 10px;border-radius:10px;background:rgba(12,10,9,0.92);border:1px solid rgba(251,191,36,0.35);font-size:0.72rem;font-family:'JetBrains Mono',monospace;color:#e7e5e4;"
      :style="{ left: Math.min(chartHover.x + 12, cw - 160) + 'px', top: '48px' }">
      <div style="color:#fbbf24;margin-bottom:4px;">{{ chartHover.label }}</div>
      <div v-for="p in chartHover.points" :key="p.key" style="display:flex;justify-content:space-between;gap:12px;">
        <span :style="{color:p.color}">{{ p.label }}</span><span>{{ fmtPct(p.value) }}</span>
      </div>
    </div>
  </div>
</div>

<script>
export default {
  data() {
    return {
      chartRange: '25h',
      chartHover: null,
      cw: 720,
      ch: 260,
      padL: 36,
      padR: 12,
      padT: 12,
      padB: 28
    };
  },
  watch: {
    msg: {
      deep: true,
      handler() { this.chartHover = null; }
    }
  },
  computed: {
    snap() { return (this.msg && this.msg.payload) || {}; },
    hostName() { return this.snap.host || 'automation'; },
    ageLabel() {
      const ts = this.snap.timestamp;
      if (!ts) return 'waiting for metrics…';
      const age = Math.max(0, Date.now() - new Date(ts).getTime());
      const s = Math.floor(age / 1000);
      if (s < 60) return 'updated ' + s + 's ago';
      return 'updated ' + Math.floor(s / 60) + 'm ago · ' + new Date(ts).toLocaleString();
    },
    gauges() {
      const d = this.snap;
      const root = d.disk && d.disk.root;
      const data = d.disk && d.disk.data;
      const load1 = d.load && d.load['1'];
      return [
        { key: 'cpu', label: 'CPU', value: d.cpu && d.cpu.percent, color: '#38bdf8', sub: (d.cpu && d.cpu.count ? d.cpu.count + ' cores' : '—') },
        { key: 'mem', label: 'Memory', value: d.memory && d.memory.percent, color: '#fbbf24', sub: this.fmtBytes(d.memory && d.memory.used_bytes) + ' / ' + this.fmtBytes(d.memory && d.memory.total_bytes) },
        { key: 'root', label: 'Disk /', value: root && root.percent, color: '#fb7185', sub: this.fmtBytes(root && root.used_bytes) + ' / ' + this.fmtBytes(root && root.total_bytes) },
        { key: 'data', label: 'Disk /data', value: data && data.percent, color: '#34d399', sub: data ? (this.fmtBytes(data.used_bytes) + ' / ' + this.fmtBytes(data.total_bytes)) : 'not mounted' },
        { key: 'load', label: 'Load 1m', value: load1 != null ? Math.min(100, (load1 / Math.max(1, (d.cpu && d.cpu.count) || 1)) * 100) : null, color: '#a78bfa', sub: load1 != null ? ('avg ' + Number(load1).toFixed(2)) : '—' }
      ];
    },
    chartRanges() {
      return [
        { key: '1h', label: '1 hour' },
        { key: '25h', label: '25 hours' },
        { key: '1m', label: '1 month' }
      ];
    },
    chartTitle() {
      if (this.chartRange === '1h') return 'Last hour (1‑min buckets)';
      if (this.chartRange === '25h') return 'Last 25 hours (1‑min buckets)';
      return 'Last month (1‑hour buckets)';
    },
    seriesMeta() {
      return [
        { key: 'cpu', label: 'CPU', color: '#38bdf8' },
        { key: 'mem', label: 'Memory', color: '#fbbf24' },
        { key: 'root', label: 'Disk /', color: '#fb7185' },
        { key: 'dataDisk', label: 'Disk /data', color: '#34d399' }
      ];
    },
    chartPoints() {
      const now = Date.now();
      if (this.chartRange === '1m') {
        const src = this.snap.month_chart || [];
        const cutoff = now - 31 * 24 * 3600 * 1000;
        return src.filter(p => p && p.t >= cutoff);
      }
      const src = this.snap.fine_chart || [];
      const win = this.chartRange === '1h' ? 3600 * 1000 : 25 * 3600 * 1000;
      const cutoff = now - win;
      return src.filter(p => p && p.t >= cutoff);
    },
    plotW() { return this.cw - this.padL - this.padR; },
    plotH() { return this.ch - this.padT - this.padB; },
    xDomain() {
      const pts = this.chartPoints;
      if (!pts.length) {
        const now = Date.now();
        const win = this.chartRange === '1h' ? 3600e3 : (this.chartRange === '25h' ? 25 * 3600e3 : 31 * 24 * 3600e3);
        return { min: now - win, max: now };
      }
      return { min: pts[0].t, max: pts[pts.length - 1].t };
    },
    yTicks() {
      return [0, 25, 50, 75, 100].map(v => ({ v, y: this.yScale(v) }));
    },
    xTicks() {
      const { min, max } = this.xDomain;
      const span = Math.max(1, max - min);
      const count = this.chartRange === '1h' ? 4 : (this.chartRange === '25h' ? 5 : 6);
      const ticks = [];
      for (let i = 0; i <= count; i++) {
        const t = min + (span * i) / count;
        ticks.push({ t, x: this.xScale(t), label: this.fmtTick(t) });
      }
      return ticks;
    },
    seriesPaths() {
      return this.seriesMeta.map(s => ({
        key: s.key,
        color: s.color,
        d: this.buildPath(s.key)
      }));
    }
  },
  methods: {
    setChartRange(key) { this.chartRange = key; this.chartHover = null; },
    chartRangeBtnStyle(key) {
      const on = this.chartRange === key;
      return {
        border: '1px solid ' + (on ? 'rgba(251,191,36,0.55)' : 'rgba(255,255,255,0.12)'),
        background: on ? 'rgba(251,191,36,0.18)' : 'rgba(255,255,255,0.05)',
        color: on ? '#fef3c7' : '#a8a29e',
        borderRadius: '9px',
        padding: '6px 12px',
        fontSize: '0.72rem',
        fontWeight: '700',
        cursor: 'pointer',
        fontFamily: 'DM Sans, system-ui, sans-serif'
      };
    },
    fmtPct(v) {
      if (v == null || !Number.isFinite(Number(v))) return '—';
      return Number(v).toFixed(1) + '%';
    },
    fmtBytes(n) {
      if (n == null || !Number.isFinite(Number(n))) return '—';
      const u = ['B','KB','MB','GB','TB'];
      let v = Number(n), i = 0;
      while (v >= 1024 && i < u.length - 1) { v /= 1024; i++; }
      return v.toFixed(v >= 10 || i === 0 ? 0 : 1) + ' ' + u[i];
    },
    fmtTick(t) {
      const d = new Date(t);
      if (this.chartRange === '1m') return (d.getDate()) + '/' + (d.getMonth() + 1);
      if (this.chartRange === '25h') return d.getHours().toString().padStart(2,'0') + ':00';
      return d.getHours().toString().padStart(2,'0') + ':' + d.getMinutes().toString().padStart(2,'0');
    },
    xScale(t) {
      const { min, max } = this.xDomain;
      const span = Math.max(1, max - min);
      return this.padL + ((t - min) / span) * this.plotW;
    },
    yScale(v) {
      const clamped = Math.max(0, Math.min(100, Number(v) || 0));
      return this.padT + (1 - clamped / 100) * this.plotH;
    },
    buildPath(key) {
      const pts = this.chartPoints.filter(p => p[key] != null && Number.isFinite(Number(p[key])));
      if (pts.length < 2) return '';
      return pts.map((p, i) => {
        const x = this.xScale(p.t);
        const y = this.yScale(p[key]);
        return (i === 0 ? 'M' : 'L') + x.toFixed(1) + ' ' + y.toFixed(1);
      }).join(' ');
    },
    arcPath(pct) {
      const v = Math.max(0, Math.min(100, Number(pct) || 0));
      const start = Math.PI;
      const end = Math.PI + Math.PI * (v / 100);
      const cx = 60, cy = 64, r = 46;
      const x1 = cx + r * Math.cos(start);
      const y1 = cy + r * Math.sin(start);
      const x2 = cx + r * Math.cos(end);
      const y2 = cy + r * Math.sin(end);
      const large = v > 50 ? 1 : 0;
      return 'M ' + x1 + ' ' + y1 + ' A ' + r + ' ' + r + ' 0 ' + large + ' 1 ' + x2 + ' ' + y2;
    },
    onChartMove(ev) {
      const svg = ev.currentTarget;
      const rect = svg.getBoundingClientRect();
      const x = ((ev.clientX - rect.left) / rect.width) * this.cw;
      this.updateHover(x);
    },
    onChartTouch(ev) {
      if (!ev.touches || !ev.touches[0]) return;
      const svg = ev.currentTarget;
      const rect = svg.getBoundingClientRect();
      const x = ((ev.touches[0].clientX - rect.left) / rect.width) * this.cw;
      this.updateHover(x);
    },
    updateHover(x) {
      const pts = this.chartPoints;
      if (!pts.length) { this.chartHover = null; return; }
      const { min, max } = this.xDomain;
      const span = Math.max(1, max - min);
      const t = min + ((x - this.padL) / this.plotW) * span;
      let best = pts[0], bestDist = Math.abs(pts[0].t - t);
      for (const p of pts) {
        const d = Math.abs(p.t - t);
        if (d < bestDist) { best = p; bestDist = d; }
      }
      const points = this.seriesMeta
        .filter(s => best[s.key] != null)
        .map(s => ({ key: s.key, label: s.label, color: s.color, value: best[s.key], y: this.yScale(best[s.key]) }));
      this.chartHover = {
        x: this.xScale(best.t),
        label: new Date(best.t).toLocaleString(),
        points
      };
    }
  }
};
</script>`;

const nodes = [
  {
    id: "host_metrics_comment",
    type: "comment",
    z: "tab_dashboard",
    name: "═══════════════ HOST METRICS (910) ═══════════════",
    info: "## Automation host metrics\n\n**Flow:** 910\n**MQTT:** `system/automation/status`\n**Service:** `host-metrics-publisher.service`\n**UI:** `/dashboard/host`\n\nCharts: 1 hour · 25 hours · 1 month.",
    x: 260,
    y: 40,
    wires: [],
  },
  {
    id: "ui_page_host_metrics",
    type: "ui-page",
    name: "Host",
    ui: "ui_base",
    path: "/host",
    icon: "server",
    layout: "grid",
    theme: "39a2cf2c0af73875",
    order: 8,
    className: "",
    visible: "true",
    disabled: "false",
  },
  {
    id: "ui_group_host_metrics",
    type: "ui-group",
    name: "System resources",
    page: "ui_page_host_metrics",
    width: "12",
    height: "1",
    order: 1,
    showTitle: true,
    className: "",
    visible: "true",
    disabled: "false",
  },
  {
    id: "host_metrics_mqtt_in",
    type: "mqtt in",
    z: "tab_dashboard",
    name: "system/automation/status",
    topic: "system/automation/status",
    qos: "1",
    datatype: "json",
    broker: "mqtt_broker_local",
    nl: false,
    rap: true,
    rh: 0,
    inputs: 0,
    x: 180,
    y: 140,
    wires: [["host_metrics_process"]],
  },
  {
    id: "host_metrics_process",
    type: "function",
    z: "tab_dashboard",
    name: "Bucket history + forward",
    func: PROCESS_FUNC,
    outputs: 1,
    timeout: 0,
    noerr: 0,
    initialize: "",
    finalize: "",
    libs: [],
    x: 440,
    y: 140,
    wires: [["host_metrics_ui"]],
  },
  {
    id: "host_metrics_refresh",
    type: "inject",
    z: "tab_dashboard",
    name: "Refresh UI 15s",
    props: [{ p: "payload" }, { p: "topic", vt: "str" }],
    repeat: "15",
    crontab: "",
    once: true,
    onceDelay: 2,
    topic: "refresh",
    payload: "",
    payloadType: "date",
    x: 180,
    y: 220,
    wires: [["host_metrics_refresh_fn"]],
  },
  {
    id: "host_metrics_refresh_fn",
    type: "function",
    z: "tab_dashboard",
    name: "Replay last snapshot",
    func: REFRESH_FUNC,
    outputs: 1,
    timeout: 0,
    noerr: 0,
    initialize: "",
    finalize: "",
    libs: [],
    x: 440,
    y: 220,
    wires: [["host_metrics_ui"]],
  },
  {
    id: "host_metrics_ui",
    type: "ui-template",
    z: "tab_dashboard",
    group: "ui_group_host_metrics",
    page: "",
    ui: "",
    name: "Host metrics dashboard",
    order: 1,
    width: "12",
    height: "12",
    head: "",
    format: TEMPLATE,
    storeOutMessages: true,
    passthru: false,
    resendOnRefresh: true,
    templateScope: "local",
    className: "",
    x: 700,
    y: 180,
    wires: [[]],
  },
];

writeFileSync(outFile, JSON.stringify(nodes, null, 4) + "\n");
console.log("Wrote", outFile, "(" + nodes.length + " nodes)");
