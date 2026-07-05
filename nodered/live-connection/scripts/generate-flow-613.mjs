import { writeFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const outFile = join(
  dirname(fileURLToPath(import.meta.url)),
  "..",
  "..",
  "flows",
  "613-watchdog-status-dashboard.json"
);

const NR_WATCHDOGS = [
  { id: "watchdog_maingate", name: "Main Gate", category: "Gates", topic: "MainGate/STAT/reccurentStatusRelay4", timeoutMin: 3 },
  { id: "watchdog_sliding", name: "Primary Sliding Gate", category: "Gates", topic: "tele/LuncaCetatuiiSlidingGateAutomation/STATE", timeoutMin: 11 },
  { id: "watchdog_secondary", name: "Secondary Sliding Gate", category: "Gates", topic: "tele/portaSecundara/STATE", timeoutMin: 11 },
  { id: "watchdog_irrigation", name: "Irrigation System", category: "Garden", topic: "tele/IrigationSystem/STATE", timeoutMin: 11 },
  { id: "watchdog_pump", name: "Water Pump", category: "Garden", topic: "tele/pompaApa/STATE", timeoutMin: 11 },
  { id: "watchdog_garden_power", name: "Garden Power", category: "Garden", topic: "tele/sonoffPower320D_afara/STATE", timeoutMin: 11 },
  { id: "watchdog_garden_lights", name: "Garden Lights", category: "Garden", topic: "tele/GardenAutomationLights/STATE", timeoutMin: 11 },
  { id: "watchdog_front_house", name: "Front House Power", category: "Garden", topic: "tele/frontHousePower/STATE", timeoutMin: 11 },
  { id: "watchdog_aquarium", name: "Aquarium Light", category: "Garden", topic: "tele/sursaAcvariu/STATE", timeoutMin: 11 },
  { id: "watchdog_victron", name: "Victron Energy", category: "Energy", topic: "energy/victron/status", timeoutMin: 2 },
  { id: "watchdog_huawei", name: "Huawei Solar", category: "Energy", topic: "energy/huawei/status", timeoutMin: 2 },
  { id: "watchdog_scala1", name: "Grundfos SCALA1", category: "Water", topic: "water/grundfos/scala1/status", timeoutMin: 2 },
  { id: "watchdog_sms_gateway", name: "SMS Gateway", category: "Comms", topic: "sms/gateway/status", timeoutMin: 5 },
];

const MQTT_SUBS = [
  { id: "watchdog_ui_in_maingate", name: "Main gate HB", topic: "MainGate/STAT/reccurentStatusRelay4" },
  { id: "watchdog_ui_in_tasmota", name: "Tasmota STATE", topic: "tele/+/STATE" },
  { id: "watchdog_ui_in_energy", name: "Energy status", topic: "energy/+/status" },
  { id: "watchdog_ui_in_scala1", name: "SCALA1 status", topic: "water/grundfos/scala1/status" },
  { id: "watchdog_ui_in_sms_gw", name: "SMS gateway status", topic: "sms/gateway/status" },
  { id: "watchdog_ui_in_cameras", name: "Camera health", topic: "garden/camera/+/health" },
  { id: "watchdog_ui_in_sms_wd", name: "SMS watchdog status", topic: "sms/gateway/watchdog/status" },
];

const BUILD_FUNC = `const NR_WATCHDOGS = ${JSON.stringify(NR_WATCHDOGS)};

const CAMERA_LABELS = {
    interior: 'Interior curte',
    smallGate: 'Poarta mica',
    backyard: 'Spate casa',
    gate2: 'Poarta glisanta 2',
    gate1: 'Poarta glisanta 1',
    fataCasa: 'Fata casa',
    strada: 'Curte strada'
};

function displayName(slug) {
    if (CAMERA_LABELS[slug]) return CAMERA_LABELS[slug];
    return slug.replace(/_/g, ' ').replace(/([a-z])([A-Z])/g, '$1 $2')
        .replace(/\\b\\w/g, c => c.toUpperCase());
}

function resolveState(id, timeoutMin) {
    const stateKey = id.startsWith('camera_')
        ? 'watchdog_state_' + id
        : 'watchdog_state_' + id;
    let state = flow.get(stateKey) || 'unknown';
    const lastKey = id.startsWith('camera_')
        ? 'watchdog_ui_last_' + id
        : 'watchdog_ui_last_' + id;
    const lastSeen = flow.get(lastKey);
    if ((!state || state === 'unknown') && lastSeen) {
        const ageMin = (Date.now() - lastSeen) / 60000;
        if (ageMin <= timeoutMin) state = 'online';
        else state = 'offline';
    }
    return { state, lastSeen: lastSeen || null };
}

const items = [];

for (const d of NR_WATCHDOGS) {
    const { state, lastSeen } = resolveState(d.id, d.timeoutMin);
    items.push({
        id: d.id,
        name: d.name,
        category: d.category,
        layer: 'Node-RED',
        topic: d.topic,
        timeoutMin: d.timeoutMin,
        state,
        lastSeen
    });
}

for (const slug of Object.keys(CAMERA_LABELS)) {
    const id = 'camera_' + slug;
    const { state, lastSeen } = resolveState(id, 2);
    items.push({
        id,
        name: displayName(slug),
        category: 'Cameras',
        layer: 'Node-RED',
        topic: 'garden/camera/' + slug + '/health',
        timeoutMin: 2,
        state,
        lastSeen
    });
}

const smsDevices = flow.get('watchdog_sms_devices') || [];
for (const dev of smsDevices) {
    if (!dev || !dev.name) continue;
    items.push({
        id: 'sms_hw_' + dev.name,
        name: dev.name,
        category: dev.name.startsWith('camera_') ? 'Cameras' : 'SMS Gateway',
        layer: 'SMS Hardware',
        topic: 'sms/gateway/watchdog/heartbeat',
        timeoutMin: Math.max(1, Math.round((dev.interval || 60) / 60)),
        timeoutSec: dev.interval || 60,
        state: dev.online ? 'online' : 'offline',
        lastSeen: dev.lastSeen || null,
        ageSec: dev.ageSec
    });
}

items.sort((a, b) => {
    const c = a.category.localeCompare(b.category);
    if (c !== 0) return c;
    return a.name.localeCompare(b.name);
});

const summary = items.reduce((acc, it) => {
    acc[it.state] = (acc[it.state] || 0) + 1;
    return acc;
}, { online: 0, offline: 0, unknown: 0 });

msg.payload = {
    items,
    summary,
    updatedAt: new Date().toISOString()
};
return msg;`;

const TOUCH_FUNC = `const NR_WATCHDOGS = ${JSON.stringify(NR_WATCHDOGS)};

const TOPIC_TO_ID = {};
for (const d of NR_WATCHDOGS) TOPIC_TO_ID[d.topic] = d.id;

const topic = msg.topic || '';
const now = Date.now();

if (topic === 'sms/gateway/watchdog/status') {
    let list = msg.payload;
    if (typeof list === 'string') {
        try { list = JSON.parse(list); } catch (e) { list = []; }
    }
    if (!Array.isArray(list)) list = [];
    const normalized = list.map(dev => ({
        name: dev.name,
        interval: dev.interval || 60,
        online: !!dev.online,
        ageSec: dev.age != null ? Number(dev.age) : null,
        lastSeen: dev.age != null ? now - Number(dev.age) * 1000 : null
    }));
    flow.set('watchdog_sms_devices', normalized);
    return { payload: 'refresh' };
}

if (topic.startsWith('garden/camera/') && topic.endsWith('/health')) {
    const slug = topic.split('/')[2];
    if (slug) {
        flow.set('watchdog_ui_last_camera_' + slug, now);
        const state = String(msg.payload || '').toLowerCase();
        if (state === 'online' || state === 'offline') {
            flow.set('watchdog_state_camera_' + slug, state);
        }
    }
    return { payload: 'refresh' };
}

const id = TOPIC_TO_ID[topic];
if (id) {
    flow.set('watchdog_ui_last_' + id, now);
    return { payload: 'refresh' };
}

return null;`;

const UI_TEMPLATE = `<template>
    <div class="watchdog-dash watchdog-status-root" v-if="msg.payload">
        <div class="wd-header">
            <div>
                <div class="wd-title">⏱️ Watchdog Status</div>
                <div class="wd-subtitle">Node-RED · cameras · SMS gateway</div>
            </div>
            <div class="wd-updated" v-if="msg.payload.updatedAt">Updated {{ formatTime(msg.payload.updatedAt) }}</div>
        </div>

        <div class="wd-summary">
            <div class="wd-pill online">🟢 {{ msg.payload.summary.online || 0 }}</div>
            <div class="wd-pill offline">🔴 {{ msg.payload.summary.offline || 0 }}</div>
            <div class="wd-pill unknown">⚪ {{ msg.payload.summary.unknown || 0 }}</div>
            <div class="wd-pill total">{{ (msg.payload.items || []).length }} total</div>
        </div>

        <div class="wd-categories-wrap">
            <div v-for="(group, category) in groupedItems" :key="category" class="wd-category">
                <div class="wd-category-title">{{ category }}</div>
                <div class="wd-grid">
                    <div v-for="item in group" :key="item.id"
                         class="wd-card" :class="item.state" :title="item.topic">
                        <div class="wd-card-row">
                            <span class="wd-icon">{{ item.state === 'online' ? '🟢' : (item.state === 'offline' ? '🔴' : '⚪') }}</span>
                            <span class="wd-name">{{ item.name }}</span>
                            <span class="wd-state">{{ (item.state || 'unknown').toUpperCase() }}</span>
                        </div>
                        <div class="wd-meta">{{ item.layer }} · {{ item.timeoutSec ? item.timeoutSec + 's' : item.timeoutMin + 'm' }} · {{ formatLast(item) }}</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    computed: {
        groupedItems() {
            const groups = {};
            const items = (this.msg && this.msg.payload && this.msg.payload.items) || [];
            for (const item of items) {
                const cat = item.category || 'Other';
                if (!groups[cat]) groups[cat] = [];
                groups[cat].push(item);
            }
            return groups;
        }
    },
    methods: {
        formatTime(value) {
            if (!value) return '--:--:--';
            try {
                const d = typeof value === 'number' ? new Date(value) : new Date(value);
                return d.toLocaleTimeString('en-US', {
                    hour12: false,
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                });
            } catch (e) {
                return '--:--:--';
            }
        },
        formatLast(item) {
            if (item.lastSeen) return this.formatTime(item.lastSeen);
            if (item.ageSec != null) return item.ageSec + 's ago';
            return 'no signal';
        }
    }
}
</script>

<style>
.watchdog-dash.watchdog-status-root {
    background: #ffffff;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
    padding: 12px 14px 14px;
    color: #0f172a;
    font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    box-sizing: border-box;
    overflow: visible;
    height: auto;
    min-height: 0;
    max-height: none;
}
.watchdog-dash .wd-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 10px;
    padding-bottom: 8px;
    border-bottom: 1px solid #e2e8f0;
}
.watchdog-dash .wd-title { font-weight: 700; font-size: 1rem; color: #0f172a; }
.watchdog-dash .wd-subtitle { font-size: 0.72rem; color: #64748b; margin-top: 2px; }
.watchdog-dash .wd-updated { font-size: 0.72rem; color: #64748b; white-space: nowrap; }
.watchdog-dash .wd-summary {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 12px;
}
.watchdog-dash .wd-pill {
    font-size: 0.72rem;
    font-weight: 600;
    padding: 4px 9px;
    border-radius: 999px;
    border: 1px solid #e2e8f0;
    background: #f8fafc;
}
.watchdog-dash .wd-pill.online { color: #047857; background: #ecfdf5; border-color: #a7f3d0; }
.watchdog-dash .wd-pill.offline { color: #b91c1c; background: #fef2f2; border-color: #fecaca; }
.watchdog-dash .wd-pill.unknown { color: #475569; }
.watchdog-dash .wd-pill.total { color: #334155; }
.watchdog-dash .wd-categories-wrap {
    display: grid;
    grid-template-columns: 1fr;
    gap: 8px;
}
@media (min-width: 768px) {
    .watchdog-dash .wd-categories-wrap {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}
@media (min-width: 1200px) {
    .watchdog-dash .wd-categories-wrap {
        grid-template-columns: repeat(3, minmax(0, 1fr));
    }
}
.watchdog-dash .wd-category { margin-bottom: 0; }
.watchdog-dash .wd-category-title {
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #64748b;
    margin-bottom: 6px;
}
.watchdog-dash .wd-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 5px;
}
@media (min-width: 1024px) {
    .watchdog-dash .wd-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}
.watchdog-dash .wd-card {
    border-radius: 8px;
    padding: 8px 10px;
    border: 1px solid #e2e8f0;
    background: #f8fafc;
    border-left: 3px solid #94a3b8;
}
.watchdog-dash .wd-card.online { background: #ecfdf5; border-color: #a7f3d0; border-left-color: #059669; }
.watchdog-dash .wd-card.offline { background: #fef2f2; border-color: #fecaca; border-left-color: #dc2626; }
.watchdog-dash .wd-card.unknown { background: #f8fafc; border-left-color: #94a3b8; }
.watchdog-dash .wd-card-row {
    display: flex;
    align-items: center;
    gap: 6px;
    min-width: 0;
    margin-bottom: 3px;
}
.watchdog-dash .wd-icon { flex-shrink: 0; font-size: 0.85rem; line-height: 1; }
.watchdog-dash .wd-name {
    flex: 1;
    min-width: 0;
    font-weight: 700;
    font-size: 0.76rem;
    color: #0f172a;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.watchdog-dash .wd-state {
    flex-shrink: 0;
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.03em;
    color: #475569;
}
.watchdog-dash .wd-card.online .wd-state { color: #047857; }
.watchdog-dash .wd-card.offline .wd-state { color: #b91c1c; }
.watchdog-dash .wd-meta {
    font-size: 0.64rem;
    color: #64748b;
    line-height: 1.25;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.nrdb-ui-group.watchdog-status-group,
.nrdb-ui-group.watchdog-status-group .nrdb-ui-group-content,
.nrdb-ui-group.watchdog-status-group .nrdb-ui-widget-content,
.nrdb-ui-group.watchdog-status-group .v-card-text,
.nrdb-ui-group.watchdog-status-group .nrdb-ui-widget {
    overflow: visible !important;
    max-height: none !important;
    height: auto !important;
}
.nrdb-ui-page .nrdb-ui-group.watchdog-status-group {
    overflow: visible !important;
}
</style>`;

const nodes = [
  {
    id: "watchdog_status_comment",
    type: "comment",
    z: "8becda4e1ec6a8b9",
    name: "═══════════════ WATCHDOG STATUS DASHBOARD (613) ═══════════════",
    info: "## Watchdog Status Dashboard\n\nUnified view of all monitored devices:\n- Flow 90 MQTT watchdogs\n- Flow 612 camera watchdogs\n- SMS Gateway hardware watchdog enrollments",
    x: 340,
    y: 2280,
    wires: [],
  },
  {
    id: "ui_page_watchdog_status",
    type: "ui-page",
    z: "8becda4e1ec6a8b9",
    name: "Watchdog",
    ui: "b89dd587275b51bf",
    path: "/watchdog",
    icon: "timer-check",
    layout: "grid",
    theme: "39a2cf2c0af73875",
    breakpoints: [
      { name: "Default", px: "0", cols: "3" },
      { name: "Tablet", px: "576", cols: "6" },
      { name: "Small Desktop", px: "768", cols: "9" },
      { name: "Desktop", px: "1024", cols: "12" },
    ],
    order: 10,
    className: "",
    visible: "true",
    disabled: "false",
  },
  {
    id: "ui_group_watchdog_status",
    type: "ui-group",
    z: "8becda4e1ec6a8b9",
    name: "Watchdog Overview",
    page: "ui_page_watchdog_status",
    order: 1,
    width: "12",
    height: "1",
    showTitle: false,
    className: "watchdog-status-group",
  },
  {
    id: "inject_watchdog_ui_refresh",
    type: "inject",
    z: "8becda4e1ec6a8b9",
    name: "Refresh watchdog UI",
    props: [{ p: "payload" }],
    repeat: "30",
    crontab: "",
    once: true,
    onceDelay: 2,
    topic: "",
    payload: "",
    payloadType: "date",
    x: 180,
    y: 2360,
    wires: [["func_watchdog_ui_build"]],
  },
  {
    id: "func_watchdog_ui_touch",
    type: "function",
    z: "8becda4e1ec6a8b9",
    name: "Watchdog heartbeat touch",
    func: TOUCH_FUNC,
    outputs: 1,
    noerr: 0,
    initialize: "",
    finalize: "",
    libs: [],
    x: 430,
    y: 2440,
    wires: [["func_watchdog_ui_build"]],
  },
  {
    id: "func_watchdog_ui_build",
    type: "function",
    z: "8becda4e1ec6a8b9",
    name: "Build watchdog UI payload",
    func: BUILD_FUNC,
    outputs: 1,
    noerr: 0,
    initialize: "",
    finalize: "",
    libs: [],
    x: 690,
    y: 2360,
    wires: [["ui_watchdog_status_board"]],
  },
  {
    id: "ui_watchdog_status_board",
    type: "ui-template",
    z: "8becda4e1ec6a8b9",
    group: "ui_group_watchdog_status",
    name: "Watchdog status board",
    order: 1,
    width: 0,
    height: 0,
    format: UI_TEMPLATE,
    storeOutMessages: true,
    fwdInMessages: false,
    resendOnRefresh: true,
    templateScope: "local",
    x: 960,
    y: 2360,
    wires: [[]],
  },
];

let y = 2480;
for (const sub of MQTT_SUBS) {
  nodes.push({
    id: sub.id,
    type: "mqtt in",
    z: "8becda4e1ec6a8b9",
    name: sub.name,
    topic: sub.topic,
    qos: "1",
    datatype: sub.topic.includes("watchdog/status") ? "json" : "auto",
    broker: "mqtt_broker_local",
    nl: false,
    rap: true,
    rh: 0,
    inputs: 0,
    x: 180,
    y,
    wires: [["func_watchdog_ui_touch"]],
  });
  y += 50;
}

writeFileSync(outFile, `${JSON.stringify(nodes, null, 4)}\n`);
console.log(`Wrote ${nodes.length} nodes to ${outFile}`);
