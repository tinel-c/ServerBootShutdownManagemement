/**
 * Restyle the live SMS dashboard (http://192.168.2.4:1880/dashboard/page7).
 * Keeps the same inputs, button topics, and templates' send() payloads.
 *
 *   node nodered/live-connection/scripts/patch-sms-dashboard-ui.mjs
 */
import { readFileSync, writeFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { createClient, loadConfig } from "../src/client.mjs";

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(here, "..", "..", "..");
const flowsDir = join(repoRoot, "nodered", "flows");
const uiDir = join(flowsDir, "sms-dashboard");

const PAGE_ID = "6a925f5f6c62bcad";
const GROUP_ID = "b17a4c0a5c356134";
const STYLE_ID = "template_sms_page_style";
const LIVE_TAB = "3ad4d40302b85f75";

const css = readFileSync(join(uiDir, "page.css"), "utf8");
const statusHtml = readFileSync(join(uiDir, "status.html"), "utf8");
const watchdogHtml = readFileSync(join(uiDir, "watchdog.html"), "utf8");
const logHtml = readFileSync(join(uiDir, "log.html"), "utf8");
const callHtml = readFileSync(join(uiDir, "call.html"), "utf8");

const CALL_FUNC = `const action = msg.topic;
const phone = String(flow.get('sms_phone') || '').replace(/[^0-9]/g, '');
if (action === 'hangup') {
  msg.topic = 'sms/gateway/command/call';
  msg.payload = JSON.stringify({ action: 'hangup' });
  return msg;
}
if (action !== 'call' && action !== 'alarm') return null;
if (!phone) {
  node.warn('Phone number missing');
  return null;
}
const body = { action: action, to: phone };
if (action === 'alarm') body.times = 5;
msg.topic = 'sms/gateway/command/call';
msg.payload = JSON.stringify(body);
return msg;`;

function ensureCallNodes(nodes, { z, group }) {
  let tpl = nodes.find((n) => n.id === "template_sms_call");
  if (!tpl) {
    tpl = { id: "template_sms_call", type: "ui-template", wires: [["func_sms_call"]] };
    nodes.push(tpl);
  }
  Object.assign(tpl, {
    z,
    group,
    page: "",
    ui: "",
    name: "SMS call controls",
    order: 8,
    width: 0,
    height: 0,
    format: callHtml,
    storeOutMessages: true,
    passthru: false,
    fwdInMessages: false,
    resendOnRefresh: true,
    templateScope: "local",
    className: "sms-call",
    x: 220,
    y: 340,
    wires: [["func_sms_call"]],
  });

  let fn = nodes.find((n) => n.id === "func_sms_call");
  if (!fn) {
    fn = { id: "func_sms_call", type: "function", wires: [["mqtt_out_sms_call"]] };
    nodes.push(fn);
  }
  Object.assign(fn, {
    z,
    name: "Prepare voice call",
    func: CALL_FUNC,
    outputs: 1,
    noerr: 0,
    initialize: "",
    finalize: "",
    libs: [],
    x: 460,
    y: 340,
    wires: [["mqtt_out_sms_call"]],
  });

  let mqttOut = nodes.find((n) => n.id === "mqtt_out_sms_call");
  if (!mqttOut) {
    mqttOut = { id: "mqtt_out_sms_call", type: "mqtt out", wires: [] };
    nodes.push(mqttOut);
  }
  Object.assign(mqttOut, {
    z,
    name: "Voice call command",
    topic: "",
    qos: "1",
    retain: "",
    respTopic: "",
    contentType: "",
    userProps: "",
    correl: "",
    expiry: "",
    broker: "mqtt_broker_local",
    x: 700,
    y: 340,
    wires: [],
  });

  let mqttIn = nodes.find((n) => n.id === "mqtt_in_sms_call_status");
  if (!mqttIn) {
    mqttIn = { id: "mqtt_in_sms_call_status", type: "mqtt in", wires: [["template_sms_call"]] };
    nodes.push(mqttIn);
  }
  Object.assign(mqttIn, {
    z,
    name: "Voice call status",
    topic: "sms/gateway/call/status",
    qos: "1",
    datatype: "json",
    broker: "mqtt_broker_local",
    nl: false,
    rap: true,
    rh: 0,
    inputs: 0,
    x: 180,
    y: 400,
    wires: [["template_sms_call"]],
  });
}

function loadFlow(name) {
  const path = join(flowsDir, name);
  return { path, nodes: JSON.parse(readFileSync(path, "utf8")) };
}

function saveFlow(file) {
  writeFileSync(file.path, JSON.stringify(file.nodes, null, 4) + "\n");
}

function byId(nodes, id) {
  const node = nodes.find((n) => n.id === id);
  if (!node) throw new Error(`Missing node ${id}`);
  return node;
}

function syncRepo() {
  const controls = loadFlow("510-sms-gateway-controls.json");
  const status = loadFlow("511-sms-gateway-status.json");
  const watchdog = loadFlow("513-sms-gateway-watchdog.json");

  const phone = byId(controls.nodes, "ui_text_sms_phone");
  phone.className = "sms-phone";
  phone.order = 2;
  phone.icon = phone.icon || "phone";

  const message = byId(controls.nodes, "ui_text_sms_message");
  message.className = "sms-message";
  message.order = 3;
  message.mode = "textarea";
  message.sendOnEnter = false;
  message.icon = message.icon || "message-text";

  const send = byId(controls.nodes, "btn_sms_send");
  send.className = "sms-send";
  send.order = 4;
  send.bgcolor = "#0f766e";
  send.buttonColor = "#0f766e";
  send.textColor = "#f0fdfa";
  send.iconColor = "#f0fdfa";

  const allow = byId(controls.nodes, "ui_text_sms_allowed_phones");
  allow.className = "sms-allow";
  allow.order = 5;
  allow.icon = allow.icon || "shield-check";

  const statusNode = byId(controls.nodes, "template_sms_status");
  statusNode.className = "sms-status";
  statusNode.order = 1;
  statusNode.format = statusHtml;

  let style = controls.nodes.find((n) => n.id === STYLE_ID);
  if (!style) {
    style = {
      id: STYLE_ID,
      type: "ui-template",
      z: "tab_dashboard",
      group: "",
      page: PAGE_ID,
      ui: "",
      name: "SMS page style",
      order: 0,
      width: 0,
      height: 0,
      head: "",
      storeOutMessages: true,
      passthru: false,
      resendOnRefresh: true,
      className: "",
      x: 720,
      y: 40,
      wires: [],
    };
    controls.nodes.push(style);
  }
  style.templateScope = "page:style";
  style.format = css;
  style.page = PAGE_ID;
  style.group = "";
  style.ui = "";

  const log = byId(status.nodes, "template_sms_log");
  log.className = "sms-log";
  log.order = 7;
  log.format = logHtml;
  log.passthru = false;
  log.fwdInMessages = false;
  log.wires = [["func_clear_sms_log"]];

  const list = byId(watchdog.nodes, "template_watchdog_list");
  list.className = "sms-devices";
  list.order = 6;
  list.format = watchdogHtml;

  ensureCallNodes(controls.nodes, { z: "tab_dashboard", group: "ui_group_sms_gateway" });

  saveFlow(controls);
  saveFlow(status);
  saveFlow(watchdog);
}

function patchLive(live) {
  const page = byId(live, PAGE_ID);
  page.className = "sms-page";

  const group = byId(live, GROUP_ID);
  group.className = "sms-shell";
  group.width = 12;
  group.showTitle = false;

  const phone = byId(live, "ui_text_sms_phone");
  phone.className = "sms-phone";
  phone.order = 2;
  phone.width = 0;
  phone.icon = "phone";

  const message = byId(live, "ui_text_sms_message");
  message.className = "sms-message";
  message.order = 3;
  message.width = 0;
  message.mode = "textarea";
  message.sendOnEnter = false;
  message.icon = "message-text";

  const send = byId(live, "btn_sms_send");
  send.className = "sms-send";
  send.order = 4;
  send.width = 0;
  send.bgcolor = "#0f766e";
  send.buttonColor = "#0f766e";
  send.textColor = "#f0fdfa";
  send.iconColor = "#f0fdfa";

  const allow = byId(live, "ui_text_sms_allowed_phones");
  allow.className = "sms-allow";
  allow.order = 5;
  allow.width = 0;
  allow.icon = "shield-check";

  const statusNode = byId(live, "template_sms_status");
  statusNode.className = "sms-status";
  statusNode.order = 1;
  statusNode.width = 0;
  statusNode.format = statusHtml;

  const list = byId(live, "template_watchdog_list");
  list.className = "sms-devices";
  list.order = 6;
  list.width = 0;
  list.format = watchdogHtml;

  const log = byId(live, "template_sms_log");
  log.className = "sms-log";
  log.order = 7;
  log.width = 0;
  log.format = logHtml;
  log.passthru = false;
  log.fwdInMessages = false;
  log.wires = [["func_clear_sms_log"]];

  let style = live.find((n) => n.id === STYLE_ID);
  if (!style) {
    style = {
      id: STYLE_ID,
      type: "ui-template",
      z: LIVE_TAB,
      name: "SMS page style",
      order: 0,
      width: 0,
      height: 0,
      head: "",
      storeOutMessages: true,
      passthru: false,
      resendOnRefresh: true,
      className: "",
      x: 980,
      y: 40,
      wires: [],
    };
    live.push(style);
  }
  style.templateScope = "page:style";
  style.format = css;
  style.page = PAGE_ID;
  style.ui = "";
  style.group = "";
  style.z = style.z || LIVE_TAB;
  style.name = "SMS page style";

  ensureCallNodes(live, { z: LIVE_TAB, group: GROUP_ID });
}

syncRepo();

const client = createClient(loadConfig());
const live = await client.request("/flows");
patchLive(live);
await client.request("/flows", {
  method: "POST",
  json: live,
  headers: { "Node-RED-Deployment-Type": "full" },
});

console.log(JSON.stringify({ ok: true, page: PAGE_ID, nodes: live.length }, null, 2));
