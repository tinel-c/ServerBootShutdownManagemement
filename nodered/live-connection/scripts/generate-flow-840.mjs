import { writeFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { spawnSync } from "child_process";

const repoRoot = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const outFile = join(repoRoot, "flows", "840-energy-consumers.json");

function loadConsumers() {
  const py = spawnSync(
    process.platform === "win32" ? "python" : "python3",
    [join(repoRoot, "..", "device", "energy-consumers", "scripts", "export_registry_for_nodered.py")],
    { encoding: "utf8", cwd: join(repoRoot, "..") }
  );
  if (py.status !== 0) {
    console.error(py.stderr || py.stdout);
    throw new Error("Failed to export consumers registry");
  }
  return JSON.parse(py.stdout).consumers || [];
}

function slugId(id) {
  return id.replace(/[^a-zA-Z0-9_]/g, "_");
}

function buildTemplate(consumer) {
  const id = consumer.id;
  const accent = consumer.ui?.accent || "#38bdf8";
  const pollIntervalS = consumer.poll_interval_s || 30;
  const hasSwitch = consumer.controls?.switch !== false;
  const hasTemp = !!(consumer.dps && consumer.dps.temperature_c);
  const metricCols = hasTemp ? 5 : 4;
  const tempMetric = hasTemp
    ? `<div class="ec-metric"><div class="ec-label">°C</div><div class="ec-value">{{ formatTemp(temperatureC) }}</div></div>`
    : "";
  const switchRow = hasSwitch
    ? `<div class="ec-actions">
        <button type="button" class="ec-btn" :style="onBtnStyle" :disabled="!canControl" @click.prevent="sendSwitch('on')">ON</button>
        <button type="button" class="ec-btn" :style="offBtnStyle" :disabled="!canControl" @click.prevent="sendSwitch('off')">OFF</button>
      </div>`
    : "";

  return `<style scoped>
.ec-card { width:100%; max-width:100%; box-sizing:border-box; font-family:system-ui,-apple-system,'Segoe UI',sans-serif; color:#e2e8f0; }
.ec-inner { background:linear-gradient(160deg,#1e293b 0%,#0f172a 100%); border-radius:12px; padding:clamp(8px,2vw,12px); border:1px solid ${accent}88; box-shadow:0 4px 16px rgba(0,0,0,0.35); width:100%; }
.ec-head { display:flex; align-items:flex-start; justify-content:space-between; gap:8px; margin-bottom:8px; flex-wrap:wrap; }
.ec-title { font-size:clamp(0.85em,2.5vw,0.95em); font-weight:700; color:#f8fafc; line-height:1.2; word-break:break-word; }
.ec-id { font-size:0.62em; color:#94a3b8; margin-top:2px; font-family:ui-monospace,monospace; }
.ec-pill { padding:4px 10px; border-radius:999px; font-size:0.65em; font-weight:700; text-transform:uppercase; white-space:nowrap; color:#fff; flex-shrink:0; }
.ec-head-badges { display:flex; flex-wrap:wrap; gap:8px; align-items:center; flex-shrink:0; justify-content:flex-end; }
.ec-updated { padding:4px 10px; border-radius:8px; background:rgba(255,255,255,0.06); color:#94a3b8; font-size:0.68em; white-space:nowrap; }
.ec-updated-val { font-variant-numeric:tabular-nums; font-weight:700; }
.ec-metrics { display:grid; grid-template-columns:repeat(${metricCols},minmax(0,1fr)); gap:clamp(4px,1.5vw,8px); }
.ec-metric { background:rgba(255,255,255,0.07); border-radius:8px; padding:clamp(6px,1.5vw,8px) 4px; text-align:center; min-width:0; }
.ec-metric.power { border-top:2px solid ${accent}; background:rgba(255,255,255,0.1); }
.ec-label { font-size:0.58em; color:#cbd5e1; text-transform:uppercase; letter-spacing:0.04em; }
.ec-value { font-size:clamp(0.82em,2.2vw,1.05em); font-weight:700; color:#f8fafc; margin-top:2px; line-height:1.1; }
.ec-relay { margin-top:8px; font-size:0.72em; color:#cbd5e1; }
.ec-actions { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:8px; }
.ec-btn { appearance:none; -webkit-appearance:none; min-height:40px; padding:8px 10px; border:none; border-radius:8px; font-size:clamp(0.78em,2vw,0.85em); font-weight:700; cursor:pointer; width:100%; line-height:1.2; touch-action:manipulation; }
.ec-btn:disabled { opacity:0.45; cursor:not-allowed; }
@media (max-width:520px) { .ec-metrics { grid-template-columns:repeat(2,minmax(0,1fr)); } .ec-actions { grid-template-columns:1fr; } }
</style>
<div class="ec-card">
  <div class="ec-inner">
    <div class="ec-head">
      <div style="min-width:0;flex:1;">
        <div class="ec-title">{{ displayName }}</div>
        <div class="ec-id">${id}</div>
      </div>
      <div class="ec-head-badges">
        <div class="ec-pill" :style="onlinePillStyle">{{ onlineLabel }}</div>
        <div class="ec-updated">Updated <span class="ec-updated-val" :style="dataAgeStyle">{{ updateElapsed }}</span> ago</div>
      </div>
    </div>
    <div class="ec-metrics">
      <div class="ec-metric power"><div class="ec-label">W</div><div class="ec-value">{{ formatW(powerW) }}</div></div>
      <div class="ec-metric"><div class="ec-label">kWh</div><div class="ec-value">{{ formatKwh(energyKwh) }}</div></div>
      <div class="ec-metric"><div class="ec-label">V</div><div class="ec-value">{{ formatV(voltageV) }}</div></div>
      <div class="ec-metric"><div class="ec-label">A</div><div class="ec-value">{{ formatA(currentA) }}</div></div>
      ${tempMetric}
    </div>
    <div v-if="switchOn !== null" class="ec-relay">
      Relay <strong :style="{ color: switchOn ? '#34d399' : '#94a3b8' }">{{ switchOn ? 'ON' : 'OFF' }}</strong>
      <span v-if="breakerState"> · {{ breakerState }}</span>
      <span v-if="runMode"> · {{ runMode }}</span>
    </div>
    ${switchRow}
  </div>
</div>
<script>
export default {
  data() { return { now: Date.now(), timer: null, staleAfterS: ${pollIntervalS} * 2 }; },
  mounted() { this.timer = setInterval(() => { this.now = Date.now(); }, 1000); },
  unmounted() { clearInterval(this.timer); },
  methods: {
    formatW(v) { if (v == null || v === '') return '—'; const n = Number(v); return Number.isNaN(n) ? '—' : Math.round(n); },
    formatKwh(v) { if (v == null || v === '') return '—'; const n = Number(v); return Number.isNaN(n) ? '—' : n.toFixed(2); },
    formatV(v) { if (v == null || v === '') return '—'; const n = Number(v); return Number.isNaN(n) ? '—' : n.toFixed(1); },
    formatA(v) { if (v == null || v === '') return '—'; const n = Number(v); return Number.isNaN(n) ? '—' : n.toFixed(2); },
    formatTemp(v) { if (v == null || v === '') return '—'; const n = Number(v); return Number.isNaN(n) ? '—' : n.toFixed(1); },
    parseMs(v) {
      if (v == null || v === '') return null;
      if (typeof v === 'number' && !Number.isNaN(v)) return v;
      try { const ms = new Date(v).getTime(); return Number.isNaN(ms) ? null : ms; } catch (e) { return null; }
    },
    pad2(n) { return String(n).padStart(2, '0'); },
    sendSwitch(action) {
      if (!this.canControl) return;
      this.send({ payload: { consumer_id: '${id}', action, source: 'nodered', timestamp: new Date().toISOString() } });
    }
  },
  computed: {
    p() { return this.msg.payload || {}; },
    displayName() { return this.p.name || '${consumer.name.replace(/'/g, "\\'")}'; },
    powerW() { return this.p.power_w; },
    energyKwh() { return this.p.energy_kwh; },
    voltageV() { return this.p.voltage_v; },
    currentA() { return this.p.current_a; },
    temperatureC() { return this.p.extra && this.p.extra.temperature_c != null ? this.p.extra.temperature_c : null; },
    breakerState() { return this.p.extra && this.p.extra.breaker_state ? this.p.extra.breaker_state : ''; },
    runMode() { return this.p.extra && this.p.extra.run_mode ? this.p.extra.run_mode : ''; },
    switchOn() {
      if (this.p.extra && this.p.extra.switch_on !== undefined) return !!this.p.extra.switch_on;
      return null;
    },
    canControl() { return this.p.online !== false; },
    onlineLabel() { return this.p.online === false ? 'Offline' : 'Online'; },
    onlinePillStyle() {
      const on = this.p.online !== false;
      return { background: on ? '#059669' : '#dc2626', color: '#fff' };
    },
    onBtnStyle() {
      const lit = this.switchOn === true;
      return { background: lit ? '#047857' : '#059669', color: '#fff', boxShadow: lit ? '0 0 0 2px #34d399' : 'none' };
    },
    offBtnStyle() {
      const lit = this.switchOn === false;
      return { background: lit ? '#334155' : '#475569', color: '#f8fafc', boxShadow: lit ? '0 0 0 2px #94a3b8' : 'none' };
    },
    lastFetchedMs() {
      const meta = this.msg.metadata?.lastReportedMs;
      if (meta) return meta;
      if (this.p._fetched_at_ms) return this.p._fetched_at_ms;
      return this.parseMs(this.p.timestamp);
    },
    updateElapsed() {
      const ms = this.lastFetchedMs;
      if (!ms) return '—:—';
      void this.now;
      const sec = Math.max(0, Math.floor((this.now - ms) / 1000));
      const m = Math.floor(sec / 60);
      const s = sec % 60;
      return this.pad2(m) + ':' + this.pad2(s);
    },
    dataAgeStyle() {
      const ms = this.lastFetchedMs;
      if (!ms) return { color: '#e2e8f0' };
      void this.now;
      const s = (this.now - ms) / 1000;
      if (s > this.staleAfterS) return { color: '#fbbf24' };
      return { color: '#e2e8f0' };
    }
  }
};
</script>`;
}

const consumers = loadConsumers();
const ids = consumers.map((c) => c.id);

const FAN_OUT_FUNC = `const ids = ${JSON.stringify(ids)};
function enrich(id) {
  const payload = flow.get('consumer_status_' + id) || { consumer_id: id, name: id, online: false };
  const metadata = flow.get('consumer_meta_' + id) || {};
  let fetchedMs = metadata.lastReportedMs;
  if (!fetchedMs && payload.timestamp) {
    try { fetchedMs = new Date(payload.timestamp).getTime(); } catch (e) { fetchedMs = null; }
  }
  const enriched = fetchedMs ? { ...payload, _fetched_at_ms: fetchedMs } : payload;
  return { payload: enriched, metadata };
}
return ids.map(id => [enrich(id)]);`;

const STORE_FUNC = `const parts = (msg.topic || '').split('/');
if (parts.length < 4) return null;
const id = parts[2];
const payload = msg.payload || {};
flow.set('consumer_status_' + id, payload);
const metaKey = 'consumer_meta_' + id;
let meta = flow.get(metaKey) || {};
let reportMs;
try {
  reportMs = payload.timestamp ? new Date(payload.timestamp).getTime() : Date.now();
} catch (e) {
  reportMs = Date.now();
}
meta.lastReportedMs = reportMs;
meta.receivedAtMs = Date.now();
flow.set(metaKey, meta);
node.status({ fill: 'green', shape: 'dot', text: id + ' ' + (payload.power_w != null ? payload.power_w + 'W' : '') });
return { payload, metadata: meta };`;

const SWITCH_CMD_FUNC = `const p = msg.payload;
if (!p || typeof p !== 'object' || !p.action) return null;
const id = p.consumer_id;
if (!id) return null;
return {
  topic: 'energy/consumers/' + id + '/command/switch',
  payload: p
};`;

const nodes = [
  {
    id: "consumers_energy_comment",
    type: "comment",
    z: "tab_dashboard",
    name: "═══════════════ ENERGY CONSUMERS (840) ═══════════════",
    info: "## Energy Consumers Dashboard\\n\\n**Flow 840** — Tuya smart meters on Energy page after Huawei.\\n\\nRegenerate: `node nodered/live-connection/scripts/generate-flow-840.mjs`\\n\\nSee docs/ENERGY_CONSUMER_ADD.md",
    x: 320,
    y: 900,
    wires: [],
  },
  {
    id: "mqtt_in_consumers_status",
    type: "mqtt in",
    z: "tab_dashboard",
    name: "Consumer status",
    topic: "energy/consumers/+/status",
    qos: "1",
    datatype: "json",
    broker: "mqtt_broker_local",
    nl: false,
    rap: true,
    rh: 0,
    inputs: 0,
    x: 180,
    y: 980,
    wires: [["func_consumer_store_status"]],
  },
  {
    id: "func_consumer_store_status",
    type: "function",
    z: "tab_dashboard",
    name: "Store consumer status",
    func: STORE_FUNC,
    outputs: 1,
    noerr: 0,
    initialize: "",
    finalize: "",
    libs: [],
    x: 420,
    y: 980,
    wires: [["func_consumers_fan_out"]],
  },
  {
    id: "inject_consumers_refresh",
    type: "inject",
    z: "tab_dashboard",
    name: "Refresh consumer UIs",
    props: [{ p: "payload" }],
    repeat: "30",
    crontab: "",
    once: true,
    onceDelay: 2,
    topic: "",
    payload: "",
    payloadType: "date",
    x: 190,
    y: 1040,
    wires: [["func_consumers_fan_out"]],
  },
  {
    id: "func_consumers_fan_out",
    type: "function",
    z: "tab_dashboard",
    name: "Fan-out consumer UIs",
    func: FAN_OUT_FUNC,
    outputs: consumers.length,
    noerr: 0,
    initialize: "",
    finalize: "",
    libs: [],
    x: 440,
    y: 1040,
    wires: consumers.map((c) => [[`template_consumer_${slugId(c.id)}`]]),
  },
  {
    id: "func_consumer_switch_cmd",
    type: "function",
    z: "tab_dashboard",
    name: "Route consumer switch cmd",
    func: SWITCH_CMD_FUNC,
    outputs: 1,
    noerr: 0,
    initialize: "",
    finalize: "",
    libs: [],
    x: 700,
    y: 1120,
    wires: [["mqtt_out_consumer_cmd"]],
  },
  {
    id: "mqtt_out_consumer_cmd",
    type: "mqtt out",
    z: "tab_dashboard",
    name: "Consumer command",
    topic: "",
    qos: "1",
    retain: "",
    respTopic: "",
    contentType: "",
    userProps: "",
    correl: "",
    expiry: "",
    broker: "mqtt_broker_local",
    x: 920,
    y: 1120,
    wires: [],
  },
];

let y = 1080;
for (const consumer of consumers) {
  const sid = slugId(consumer.id);
  const order = consumer.ui?.order ?? 10;
  nodes.push({
    id: `ui_group_consumer_${sid}`,
    type: "ui-group",
    name: consumer.name,
    page: "ui_page_energy",
    width: "12",
    height: "1",
    order,
    showTitle: false,
    className: "",
    visible: "true",
    disabled: "false",
  });
  nodes.push({
    id: `template_consumer_${sid}`,
    type: "ui-template",
    z: "tab_dashboard",
    group: `ui_group_consumer_${sid}`,
    name: `${consumer.name} UI`,
    order: 1,
    width: 0,
    height: 0,
    format: buildTemplate(consumer),
    storeOutMessages: true,
    fwdInMessages: false,
    resendOnRefresh: true,
    templateScope: "local",
    className: "",
    x: 700,
    y,
    wires: [["func_consumer_switch_cmd"]],
  });
  y += 80;
}

writeFileSync(outFile, `${JSON.stringify(nodes, null, 4)}\n`);
console.log(`Wrote ${nodes.length} nodes (${consumers.length} consumer(s)) to ${outFile}`);
