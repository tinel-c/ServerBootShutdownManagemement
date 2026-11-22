/**
 * Generate flow 330 — 4-channel thyristor illumination dashboard.
 *
 *   node nodered/live-connection/scripts/generate-flow-330.mjs
 *   node nodered/live-connection/scripts/deploy-flow-330.mjs
 */
import { writeFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const outFile = join(
  dirname(fileURLToPath(import.meta.url)),
  "..",
  "..",
  "flows",
  "330-4ch-thyristor-illumination.json"
);

const TAB = "tab_4ch_thyristor";

const SHARED = `const STALE_MS = 90 * 1000;
const CHANNELS = [
    { id: 1, silk: 'RY1', gpio: 'IO32', terminal: 'L1' },
    { id: 2, silk: 'RY2', gpio: 'IO25', terminal: 'L2' },
    { id: 3, silk: 'RY3', gpio: 'IO27', terminal: 'L3' },
    { id: 4, silk: 'RY4', gpio: 'IO12', terminal: 'L4' }
];

function blankView() {
    return {
        device: 'PlatformIO_esp32-4ch-thyristor-board-illumination',
        hostname: 'esp32-4ch-thyristor',
        fw: null,
        ip: null,
        ota_port: 3232,
        outputs_enabled: null,
        rssi: null,
        channels: CHANNELS.map(c => ({ ...c, state: 'off' })),
        receivedAtMs: 0,
        statusUptimeBase: 0,
        commandAtMs: 0,
        ota: null
    };
}

function decorate(view) {
    const now = Date.now();
    const ageMs = view.receivedAtMs ? now - view.receivedAtMs : null;
    const uptime = view.receivedAtMs
        ? (view.statusUptimeBase || 0) + Math.floor((now - view.receivedAtMs) / 1000)
        : null;
    return {
        payload: {
            ...view,
            channels: view.channels,
            age_s: ageMs == null ? null : Math.floor(ageMs / 1000),
            online: ageMs != null && ageMs < STALE_MS,
            waiting: !view.receivedAtMs,
            uptime_s: uptime,
            refreshTick: now
        }
    };
}
`;

const STATUS_FUNC = `${SHARED}
let data = msg.payload;
if (typeof data === 'string') {
    try { data = JSON.parse(data); } catch (e) { return null; }
}
if (!data || !Array.isArray(data.channels)) return null;

const prev = flow.get('thyristor_view') || blankView();
let channels = CHANNELS.map(meta => {
    const found = data.channels.find(c => Number(c.id) === meta.id);
    return { ...meta, state: found && found.state === 'on' ? 'on' : 'off' };
});

const commandedAt = prev.commandAtMs || 0;
const pending = commandedAt && (Date.now() - commandedAt) < 2500;
if (pending) {
    const incoming = channels.map(c => c.state).join(',');
    const local = (prev.channels || []).map(c => c.state).join(',');
    if (incoming !== local) channels = prev.channels;
}

const view = {
    ...prev,
    device: data.device || prev.device,
    hostname: 'esp32-4ch-thyristor',
    fw: data.fw || prev.fw,
    ip: data.ip || prev.ip,
    ota_port: data.ota_port || prev.ota_port || 3232,
    outputs_enabled: data.outputs_enabled === true,
    rssi: data.rssi,
    channels,
    receivedAtMs: Date.now(),
    statusUptimeBase: Number(data.uptime_s) || 0,
    commandAtMs: pending && channels === prev.channels ? commandedAt : 0
};
flow.set('thyristor_view', view);
return decorate(view);`;

const OTA_STATUS_FUNC = `${SHARED}
let data = msg.payload;
if (typeof data === 'string') {
    try { data = JSON.parse(data); } catch (e) { return null; }
}
if (!data || !data.state) return null;
const view = flow.get('thyristor_view') || blankView();
const prev = view.ota || {};
view.ota = {
    state: data.state,
    detail: data.detail || '',
    percent: data.state === 'started' ? (prev.percent || 0) : (data.state === 'completed' ? 100 : prev.percent || null),
    at: Date.now()
};
if (data.state === 'started' && Array.isArray(view.channels)) {
    view.channels = view.channels.map(c => ({ ...c, state: 'off' }));
}
flow.set('thyristor_view', view);
return decorate(view);`;

const OTA_PROGRESS_FUNC = `${SHARED}
let data = msg.payload;
if (typeof data === 'string') {
    try { data = JSON.parse(data); } catch (e) { return null; }
}
if (!data || data.percent == null) return null;
const view = flow.get('thyristor_view') || blankView();
const prev = view.ota || {};
view.ota = {
    state: prev.state || 'started',
    detail: prev.detail || '',
    percent: Number(data.percent),
    at: Date.now()
};
flow.set('thyristor_view', view);
return decorate(view);`;

const REFRESH_FUNC = `${SHARED}
const view = flow.get('thyristor_view') || blankView();
return decorate(view);`;

const COMMAND_FUNC = `${SHARED}
const cmd = msg.payload || {};
const view = flow.get('thyristor_view') || blankView();
const otaBusy = view.ota && view.ota.state === 'started';
if (view.outputs_enabled === false || otaBusy) {
    node.warn('thyristor command ignored: outputs locked');
    return null;
}

function mqtt(channel, state) {
    return { payload: { channel, state } };
}

let messages = [];
if (cmd.action === 'all-off' || (Number(cmd.channel) === 0 && cmd.state === 'off')) {
    view.channels = view.channels.map(c => ({ ...c, state: 'off' }));
    messages = [mqtt(0, 'off')];
} else if (cmd.action === 'all-on') {
    view.channels = view.channels.map(c => ({ ...c, state: 'on' }));
    messages = [1, 2, 3, 4].map(id => mqtt(id, 'on'));
} else {
    const channel = Number(cmd.channel);
    const state = cmd.state === 'on' ? 'on' : (cmd.state === 'off' ? 'off' : null);
    if (!state || channel < 1 || channel > 4) return null;
    view.channels = view.channels.map(c => c.id === channel ? { ...c, state } : c);
    messages = [mqtt(channel, state)];
}

view.commandAtMs = Date.now();
flow.set('thyristor_view', view);
return [messages, decorate(view)];`;

const TEMPLATE = `<div class="thy-dash" style="font-family:system-ui,-apple-system,'Segoe UI',sans-serif;color:#f5f5f4;background:
  radial-gradient(900px 420px at 0% -10%, rgba(251,191,36,0.22), transparent 55%),
  radial-gradient(700px 380px at 100% 0%, rgba(249,115,22,0.16), transparent 50%),
  linear-gradient(165deg,#1c1410 0%,#292018 46%,#0c0a09 100%);
  border-radius:18px;padding:clamp(14px,2vw,22px);border:1px solid rgba(251,191,36,0.28);
  box-shadow:0 28px 50px -18px rgba(0,0,0,0.65), inset 0 1px 0 rgba(255,255,255,0.06);
  width:100%;box-sizing:border-box;">

  <div style="display:flex;flex-wrap:wrap;gap:12px;align-items:flex-start;justify-content:space-between;margin-bottom:16px;">
    <div>
      <div style="font-size:0.72rem;letter-spacing:0.16em;text-transform:uppercase;color:#fbbf24;font-weight:700;">ESP32 · BT137S</div>
      <div style="font-size:1.45rem;font-weight:700;color:#fafaf9;margin-top:4px;">4-channel illumination</div>
      <div style="font-size:0.78rem;color:#a8a29e;margin-top:4px;font-family:ui-monospace,monospace;">{{ hostname }}</div>
    </div>
    <div :style="pillStyle" style="padding:8px 14px;border-radius:999px;font-weight:700;font-size:0.78rem;letter-spacing:0.04em;">{{ pillLabel }}</div>
  </div>

  <div v-if="lockReason" style="margin-bottom:14px;padding:10px 12px;border-radius:12px;background:rgba(248,113,113,0.12);border:1px solid rgba(248,113,113,0.35);color:#fecaca;font-size:0.82rem;">
    {{ lockReason }}
  </div>

  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:16px;">
    <div v-for="m in meta" :key="m.label" style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:10px 12px;">
      <div style="font-size:0.68rem;letter-spacing:0.08em;text-transform:uppercase;color:#a8a29e;font-weight:700;">{{ m.label }}</div>
      <div style="margin-top:4px;font-family:ui-monospace,monospace;font-size:0.95rem;color:#fafaf9;">{{ m.value }}</div>
    </div>
  </div>

  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-bottom:16px;">
    <button v-for="ch in channels" :key="ch.id" type="button" :disabled="locked"
      @click="toggle(ch)"
      :style="cardStyle(ch)"
      style="text-align:left;border-radius:16px;padding:14px;cursor:pointer;transition:border-color 0.2s, background 0.2s;">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;">
        <div style="font-size:1.15rem;font-weight:700;">{{ ch.terminal }}</div>
        <div :style="stateChip(ch)" style="padding:3px 8px;border-radius:999px;font-size:0.68rem;font-weight:700;letter-spacing:0.06em;">{{ ch.state === 'on' ? 'ON' : 'OFF' }}</div>
      </div>
      <div style="margin-top:8px;font-size:0.75rem;color:#d6d3d1;font-family:ui-monospace,monospace;">{{ ch.silk }} · {{ ch.gpio }}</div>
      <div style="margin-top:10px;height:8px;border-radius:999px;background:rgba(255,255,255,0.08);overflow:hidden;">
        <div :style="{ width: ch.state === 'on' ? '100%' : '0%', background: 'linear-gradient(90deg,#fbbf24,#f97316)', height: '100%', transition: 'width 0.25s ease' }"></div>
      </div>
    </button>
  </div>

  <div style="display:flex;flex-wrap:wrap;gap:10px;align-items:center;">
    <button type="button" :disabled="locked" @click="allOn" :style="actionStyle(false)">All on</button>
    <button type="button" :disabled="locked" @click="allOff" :style="actionStyle(true)">All off</button>
    <div style="flex:1;min-width:180px;font-size:0.75rem;color:#a8a29e;">230 V on/off only. Boot and OTA force every channel off. Commands are not retained.</div>
  </div>

  <div v-if="otaLine" style="margin-top:12px;font-size:0.78rem;color:#fde68a;font-family:ui-monospace,monospace;">{{ otaLine }}</div>
</div>

<script>
export default {
  computed: {
    snap() { return (this.msg && this.msg.payload) || {}; },
    hostname() { return this.snap.hostname || 'esp32-4ch-thyristor'; },
    channels() {
      const list = this.snap.channels;
      if (list && list.length) return list;
      return [
        { id: 1, state: 'off', silk: 'RY1', gpio: 'IO32', terminal: 'L1' },
        { id: 2, state: 'off', silk: 'RY2', gpio: 'IO25', terminal: 'L2' },
        { id: 3, state: 'off', silk: 'RY3', gpio: 'IO27', terminal: 'L3' },
        { id: 4, state: 'off', silk: 'RY4', gpio: 'IO12', terminal: 'L4' }
      ];
    },
    locked() {
      return this.snap.outputs_enabled === false || (this.snap.ota && this.snap.ota.state === 'started');
    },
    lockReason() {
      if (this.snap.outputs_enabled === false) return 'Outputs are held off. GPIO map is not confirmed in firmware.';
      if (this.snap.ota && this.snap.ota.state === 'started') return 'OTA in progress. The board forces every channel off until the update finishes.';
      if (this.snap.waiting) return 'No status yet. The board publishes every 30 s and does not retain the last message. Commands still go out.';
      if (this.snap.receivedAtMs && !this.snap.online) return 'Status is stale (last report ' + this.fmtAge(this.snap.age_s) + ' ago). Commands still go out.';
      return '';
    },
    pillLabel() {
      if (this.snap.ota && this.snap.ota.state === 'started') return 'OTA';
      if (this.snap.waiting || !this.snap.receivedAtMs) return 'WAITING';
      return this.snap.online ? 'ONLINE' : 'STALE';
    },
    pillStyle() {
      const on = this.pillLabel === 'ONLINE';
      const bad = this.pillLabel === 'STALE' || this.pillLabel === 'OTA';
      return {
        background: on ? 'rgba(52,211,153,0.16)' : (bad ? 'rgba(248,113,113,0.16)' : 'rgba(251,191,36,0.16)'),
        color: on ? '#6ee7b7' : (bad ? '#fca5a5' : '#fde68a'),
        border: '1px solid ' + (on ? 'rgba(52,211,153,0.4)' : (bad ? 'rgba(248,113,113,0.4)' : 'rgba(251,191,36,0.4)'))
      };
    },
    meta() {
      const s = this.snap;
      return [
        { label: 'Firmware', value: s.fw || '—' },
        { label: 'Address', value: s.ip ? (s.ip + ':' + (s.ota_port || 3232)) : '—' },
        { label: 'Uptime', value: this.fmtUptime(s.uptime_s) },
        { label: 'Wi-Fi', value: this.fmtRssi(s.rssi) },
        { label: 'Updated', value: s.waiting || s.age_s == null ? '—' : this.fmtAge(s.age_s) + ' ago' }
      ];
    },
    otaLine() {
      const ota = this.snap.ota;
      if (!ota || !ota.state) return '';
      const pct = ota.percent == null ? '' : (' ' + ota.percent + '%');
      const detail = ota.detail ? (' · ' + ota.detail) : '';
      return 'OTA ' + ota.state + pct + detail;
    }
  },
  methods: {
    toggle(ch) {
      if (this.locked) return;
      this.send({ payload: { channel: ch.id, state: ch.state === 'on' ? 'off' : 'on' } });
    },
    allOn() {
      if (this.locked) return;
      this.send({ payload: { action: 'all-on' } });
    },
    allOff() {
      if (this.locked) return;
      this.send({ payload: { action: 'all-off' } });
    },
    cardStyle(ch) {
      const on = ch.state === 'on';
      return {
        background: on ? 'rgba(251,191,36,0.14)' : 'rgba(255,255,255,0.04)',
        border: '1px solid ' + (on ? 'rgba(251,191,36,0.55)' : 'rgba(255,255,255,0.08)'),
        color: '#fafaf9',
        opacity: this.locked ? 0.55 : 1,
        cursor: this.locked ? 'not-allowed' : 'pointer'
      };
    },
    stateChip(ch) {
      const on = ch.state === 'on';
      return {
        background: on ? 'rgba(251,191,36,0.22)' : 'rgba(255,255,255,0.06)',
        color: on ? '#fde68a' : '#a8a29e'
      };
    },
    actionStyle(danger) {
      return {
        border: '1px solid ' + (danger ? 'rgba(248,113,113,0.55)' : 'rgba(251,191,36,0.45)'),
        background: danger ? 'rgba(248,113,113,0.16)' : 'rgba(251,191,36,0.16)',
        color: danger ? '#fecaca' : '#fde68a',
        borderRadius: '10px',
        padding: '8px 14px',
        fontWeight: '700',
        cursor: this.locked ? 'not-allowed' : 'pointer',
        opacity: this.locked ? 0.55 : 1
      };
    },
    fmtAge(s) {
      if (s == null) return '—';
      if (s < 60) return s + 's';
      return Math.floor(s / 60) + 'm ' + (s % 60) + 's';
    },
    fmtUptime(s) {
      if (s == null || !Number.isFinite(Number(s))) return '—';
      const n = Math.max(0, Math.floor(Number(s)));
      const h = Math.floor(n / 3600);
      const m = Math.floor((n % 3600) / 60);
      if (h > 0) return h + 'h ' + m + 'm';
      return m + 'm ' + (n % 60) + 's';
    },
    fmtRssi(v) {
      if (v == null || !Number.isFinite(Number(v))) return '—';
      const n = Number(v);
      const q = n >= -60 ? 'strong' : (n >= -75 ? 'ok' : 'weak');
      return n + ' dBm · ' + q;
    }
  }
};
</script>`;

const nodes = [
  {
    id: "tab_4ch_thyristor",
    type: "tab",
    label: "4ch Thyristor",
    disabled: false,
    info: "Illumination dashboard for the ESP32 4-channel BT137S board.",
    env: [],
  },
  {
    id: "thyristor_comment",
    type: "comment",
    z: TAB,
    name: "═══════════════ 4CH THYRISTOR (330) ═══════════════",
    info: "## 4-channel thyristor illumination\n\n**Flow:** 330\n**UI:** `/dashboard/illumination`\n\nStatus `illumination/4ch-thyristor/status` (every 30 s, not retained).\nCommand `illumination/4ch-thyristor/command/set`.\n`channel` 0 + `off` turns every output off.\n\nBoot and OTA force all channels off.",
    x: 280,
    y: 40,
    wires: [],
  },
  {
    id: "ui_page_4ch_thyristor",
    type: "ui-page",
    name: "Illumination",
    ui: "ui_base",
    path: "/illumination",
    icon: "lightbulb-on",
    layout: "grid",
    theme: "39a2cf2c0af73875",
    breakpoints: [
      { name: "Default", px: "0", cols: "3" },
      { name: "Tablet", px: "576", cols: "6" },
      { name: "Small Desktop", px: "768", cols: "9" },
      { name: "Desktop", px: "1024", cols: "12" },
    ],
    order: 11,
    className: "",
    visible: "true",
    disabled: "false",
  },
  {
    id: "ui_group_4ch_thyristor",
    type: "ui-group",
    name: "Thyristor channels",
    page: "ui_page_4ch_thyristor",
    width: "12",
    height: "1",
    order: 1,
    showTitle: false,
    className: "",
    visible: "true",
    disabled: "false",
  },
  {
    id: "thyristor_status_in",
    type: "mqtt in",
    z: TAB,
    name: "Thyristor status",
    topic: "illumination/4ch-thyristor/status",
    qos: "1",
    datatype: "json",
    broker: "mqtt_broker_local",
    nl: false,
    rap: true,
    rh: 0,
    inputs: 0,
    x: 180,
    y: 140,
    wires: [["thyristor_status_fn"]],
  },
  {
    id: "thyristor_status_fn",
    type: "function",
    z: TAB,
    name: "Status → view",
    func: STATUS_FUNC,
    outputs: 1,
    timeout: 0,
    noerr: 0,
    initialize: "",
    finalize: "",
    libs: [],
    x: 430,
    y: 140,
    wires: [["thyristor_ui"]],
  },
  {
    id: "thyristor_ota_in",
    type: "mqtt in",
    z: TAB,
    name: "Thyristor OTA status",
    topic: "illumination/4ch-thyristor/ota/status",
    qos: "1",
    datatype: "json",
    broker: "mqtt_broker_local",
    nl: false,
    rap: false,
    rh: 0,
    inputs: 0,
    x: 190,
    y: 220,
    wires: [["thyristor_ota_fn"]],
  },
  {
    id: "thyristor_ota_fn",
    type: "function",
    z: TAB,
    name: "OTA status → view",
    func: OTA_STATUS_FUNC,
    outputs: 1,
    timeout: 0,
    noerr: 0,
    initialize: "",
    finalize: "",
    libs: [],
    x: 450,
    y: 220,
    wires: [["thyristor_ui"]],
  },
  {
    id: "thyristor_ota_progress_in",
    type: "mqtt in",
    z: TAB,
    name: "Thyristor OTA progress",
    topic: "illumination/4ch-thyristor/ota/progress",
    qos: "1",
    datatype: "json",
    broker: "mqtt_broker_local",
    nl: false,
    rap: false,
    rh: 0,
    inputs: 0,
    x: 200,
    y: 280,
    wires: [["thyristor_ota_progress_fn"]],
  },
  {
    id: "thyristor_ota_progress_fn",
    type: "function",
    z: TAB,
    name: "OTA progress → view",
    func: OTA_PROGRESS_FUNC,
    outputs: 1,
    timeout: 0,
    noerr: 0,
    initialize: "",
    finalize: "",
    libs: [],
    x: 460,
    y: 280,
    wires: [["thyristor_ui"]],
  },
  {
    id: "thyristor_refresh",
    type: "inject",
    z: TAB,
    name: "Refresh age 5s",
    props: [{ p: "payload" }, { p: "topic", vt: "str" }],
    repeat: "5",
    crontab: "",
    once: true,
    onceDelay: 1,
    topic: "refresh",
    payload: "",
    payloadType: "date",
    x: 170,
    y: 360,
    wires: [["thyristor_refresh_fn"]],
  },
  {
    id: "thyristor_refresh_fn",
    type: "function",
    z: TAB,
    name: "Replay view",
    func: REFRESH_FUNC,
    outputs: 1,
    timeout: 0,
    noerr: 0,
    initialize: "",
    finalize: "",
    libs: [],
    x: 410,
    y: 360,
    wires: [["thyristor_ui"]],
  },
  {
    id: "thyristor_ui",
    type: "ui-template",
    z: TAB,
    group: "ui_group_4ch_thyristor",
    page: "",
    ui: "",
    name: "Thyristor illumination",
    order: 1,
    width: "12",
    height: "10",
    head: "",
    format: TEMPLATE,
    storeOutMessages: true,
    passthru: false,
    resendOnRefresh: true,
    templateScope: "local",
    className: "",
    x: 720,
    y: 240,
    wires: [["thyristor_command_fn"]],
  },
  {
    id: "thyristor_command_fn",
    type: "function",
    z: TAB,
    name: "UI → command",
    func: COMMAND_FUNC,
    outputs: 2,
    timeout: 0,
    noerr: 0,
    initialize: "",
    finalize: "",
    libs: [],
    x: 960,
    y: 240,
    wires: [["thyristor_command_out"], ["thyristor_ui"]],
  },
  {
    id: "thyristor_command_out",
    type: "mqtt out",
    z: TAB,
    name: "Thyristor command",
    topic: "illumination/4ch-thyristor/command/set",
    qos: "1",
    retain: "false",
    respTopic: "",
    contentType: "",
    userProps: "",
    correl: "",
    expiry: "",
    broker: "mqtt_broker_local",
    x: 1200,
    y: 200,
    wires: [],
  },
];

writeFileSync(outFile, JSON.stringify(nodes, null, 4) + "\n");
console.log("Wrote", outFile, "(" + nodes.length + " nodes)");
