"""One-shot generator for 515-sms-domain-gateway.json. Run from repo root or any cwd."""
import json
from pathlib import Path

HANDLER = r"""let payload = msg.payload;
if (Buffer.isBuffer(payload)) payload = payload.toString('utf8');
if (typeof payload === 'string') {
    try { payload = JSON.parse(payload); } catch (e) { return null; }
}
if (!payload || !payload.command || payload.from == null) return null;

const cmd = String(payload.command).toLowerCase();
const args = Array.isArray(payload.args) ? payload.args.map(a => String(a).toLowerCase()) : [];
const to = String(payload.from).replace(/\D/g, '') || String(payload.from);

function reply(text) {
    const parts = [];
    let t = String(text || '');
    while (t.length > 150) {
        parts.push(t.substring(0, 150));
        t = t.substring(150);
    }
    if (t.length) parts.push(t);
    if (!parts.length) parts.push('OK');
    return parts.map(p => ({ payload: JSON.stringify({ to: to, text: p }), topic: 'sms/command/reply' }));
}
function mqttAndReply(topic, mqttPayload, replyText) {
    const out = reply(replyText);
    out.push({ topic: topic, payload: mqttPayload });
    return out;
}
function sendMany(mqttMsgs, replyText) {
    const out = reply(replyText);
    for (const m of mqttMsgs) out.push(m);
    return out;
}

const IRRIG_ZONE_POWER = {
    1: 'POWER2', 2: 'POWER3', 3: 'POWER4', 4: 'POWER5',
    5: 'POWER10', 6: 'POWER11', 7: 'POWER12', 8: 'POWER13',
    9: 'POWER14', 10: 'POWER15', 11: 'POWER16', 12: 'POWER17'
};
const CONSUMER_IDS = {
    'front-lights-breaker': 'front-lights-breaker',
    front: 'front-lights-breaker',
    flb: 'front-lights-breaker',
    'breaker-inside': 'breaker-inside',
    inside: 'breaker-inside',
    'breaker-outside': 'breaker-outside',
    outside: 'breaker-outside',
    'garden-power-hut': 'garden-power-hut',
    hut: 'garden-power-hut',
    'garden-hut': 'garden-power-hut'
};

if (cmd === 'boot') {
    const server = (args[0] || 'dell');
    if (server === 'hp' || server === 'dl360p') {
        return mqttAndReply('hp/dl360p/command/boot', { action: 'boot', method: 'ilo', source: 'sms' }, 'Booting HP DL360p...');
    }
    if (server === 'media' || server === 'media_server') {
        return mqttAndReply('media/server/command/boot', { action: 'boot', source: 'sms' }, 'Booting Media Server...');
    }
    return mqttAndReply('dell/t310/command/boot', { action: 'boot', method: 'wol', source: 'sms' }, 'Booting Dell T310...');
}
if (cmd === 'shutdown' || cmd === 'stop') {
    const server = (args[0] || 'dell');
    if (server === 'hp' || server === 'dl360p') {
        return mqttAndReply('hp/dl360p/command/shutdown', { action: 'shutdown', type: 'graceful', timeout: 300, source: 'sms' }, 'Shutdown HP DL360p...');
    }
    if (server === 'media' || server === 'media_server') {
        return mqttAndReply('media/server/command/shutdown', { action: 'shutdown', type: 'graceful', source: 'sms' }, 'Shutdown Media Server...');
    }
    return mqttAndReply('dell/t310/command/shutdown', { action: 'shutdown', type: 'graceful', timeout: 300, source: 'sms' }, 'Shutdown Dell T310...');
}
if (cmd === 'force' || cmd === 'force_shutdown') {
    const server = (args[0] || 'dell');
    if (server === 'hp' || server === 'dl360p') {
        return mqttAndReply('hp/dl360p/command/shutdown', { action: 'shutdown', type: 'force', source: 'sms' }, 'FORCE shutdown HP!');
    }
    if (server === 'media' || server === 'media_server') {
        return mqttAndReply('media/server/command/shutdown', { action: 'shutdown', type: 'force', source: 'sms' }, 'FORCE shutdown Media!');
    }
    return mqttAndReply('dell/t310/command/shutdown', { action: 'shutdown', type: 'force', source: 'sms' }, 'FORCE shutdown Dell!');
}
if (cmd === 'status' || cmd === 'state') {
    const dell = flow.get('status_dell_t310_status') || {};
    const hp = flow.get('status_hp_dl360p_status') || {};
    const media = flow.get('status_media_server_status') || {};
    const d = (dell.server_state || 'unknown').toUpperCase();
    const h = (hp.server_state || 'unknown').toUpperCase();
    const m = (media.server_state || 'unknown').toUpperCase();
    return reply('Servers: Dell=' + d + ' HP=' + h + ' Media=' + m);
}

if (cmd === 'gate_open' || cmd === 'gate') {
    return mqttAndReply('MainGate/CMD/Relay3', 'ON', 'Opening Main Gate...');
}
if (cmd === 'gate_status') {
    const g = (flow.get('gate_state') || {}).mainGate || {};
    return reply('Main Gate: Power=' + (g.power||'?') + ' R1=' + (g.relay1||'?') + ' R2=' + (g.relay2||'?') + ' R3=' + (g.relay3||'?') + ' R4=' + (g.relay4||'?'));
}

if (cmd === 'sliding_open') return mqttAndReply('cmnd/automatizare_poarta/Power1', true, 'Sliding OPEN...');
if (cmd === 'sliding_close') return mqttAndReply('cmnd/automatizare_poarta/Power2', true, 'Sliding CLOSE...');
if (cmd === 'sliding_trigger') return mqttAndReply('cmnd/automatizare_poarta/Power3', true, 'Sliding TRIGGER...');
if (cmd === 'sliding_status') {
    const s = flow.get('sliding_gate_state') || {};
    return reply('Sliding: R1=' + (s.relay1||'?') + ' R2=' + (s.relay2||'?') + ' R3=' + (s.relay3||'?') + ' R4=' + (s.relay4||'?'));
}

if (cmd === 'secondary_open') return mqttAndReply('SecondGate/CMD/Relay2', 'ON', 'Secondary OPEN...');
if (cmd === 'secondary_close') return mqttAndReply('SecondGate/CMD/Relay1', 'ON', 'Secondary CLOSE...');
if (cmd === 'secondary_trigger') return mqttAndReply('SecondGate/CMD/Relay3', 'ON', 'Secondary TRIGGER...');
if (cmd === 'secondary_stop') return mqttAndReply('SecondGate/CMD/Relay4', 'ON', 'Secondary STOP...');
if (cmd === 'secondary_light_left') return mqttAndReply('SecondGate/CMD/Relay5', 'ON', 'Left light ON 120s...');
if (cmd === 'secondary_light_right') return mqttAndReply('SecondGate/CMD/Relay6', 'ON', 'Right light ON 120s...');
if (cmd === 'secondary_status') {
    const s = flow.get('secondary_gate_state') || {};
    return reply('Secondary: R1=' + (s.relay1||'?') + ' R2=' + (s.relay2||'?') + ' R3=' + (s.relay3||'?') + ' R4=' + (s.relay4||'?') + ' L=' + (s.relay5||'?') + ' R=' + (s.relay6||'?'));
}

if (cmd === 'garden_on') return mqttAndReply('cmnd/sonoffPower320D_afara/Power', 'ON', 'Garden power ON...');
if (cmd === 'garden_off') return mqttAndReply('cmnd/sonoffPower320D_afara/Power', 'OFF', 'Garden power OFF...');
if (cmd === 'garden_toggle') return mqttAndReply('cmnd/sonoffPower320D_afara/Power', 'TOGGLE', 'Garden power TOGGLE...');
if (cmd === 'garden_status') {
    const g = global.get('garden_power_state') || {};
    return reply('Garden Power: ' + (g.powerStatus||'?') + ' V=' + (g.voltage||'?') + ' A=' + (g.current||'?') + ' W=' + (g.power||'?'));
}

if (cmd === 'lights_on' || cmd === 'lights_off') {
    const state = cmd === 'lights_on' ? 'ON' : 'OFF';
    const msgs = [];
    for (let i = 1; i <= 12; i++) msgs.push({ topic: 'GardenAutomationLights/CMD/Relay' + i, payload: state });
    for (let i = 1; i <= 4; i++) msgs.push({ topic: 'cmnd/frontHousePower/POWER' + i, payload: state });
    return sendMany(msgs, 'All 16 lights ' + state + '...');
}
if (cmd === 'lights_status') {
    const st = global.get('garden_lights_state') || {};
    let on = 0, off = 0;
    for (let i = 1; i <= 16; i++) {
        if (st['light_' + i] === 'ON') on++;
        else if (st['light_' + i] === 'OFF') off++;
    }
    return reply('Lights: ' + on + ' ON, ' + off + ' OFF, ' + (16 - on - off) + ' unknown');
}
if (cmd === 'light') {
    const n = parseInt(args[0], 10);
    const state = (args[1] || '').toUpperCase();
    if (!(n >= 1 && n <= 16) || (state !== 'ON' && state !== 'OFF')) {
        return reply('Usage: LIGHT 1-16 ON|OFF');
    }
    if (n <= 12) return mqttAndReply('GardenAutomationLights/CMD/Relay' + n, state, 'Light ' + n + ' ' + state);
    return mqttAndReply('cmnd/frontHousePower/POWER' + (n - 12), state, 'Light ' + n + ' ' + state);
}

if (cmd === 'illum_status') {
    const ill = flow.get('sms_illum_status') || {};
    const ch = Array.isArray(ill.channels) ? ill.channels : [];
    if (!ch.length) return reply('Illum: no status yet');
    const parts = ch.map(c => 'C' + c.id + '=' + String(c.state || '?').toUpperCase());
    return reply('Illum: ' + parts.join(' ') + ' fw=' + (ill.fw || '?'));
}
if (cmd === 'illum') {
    if (args.length === 1 && args[0] === 'off') {
        return mqttAndReply('illumination/4ch-thyristor/command/set', JSON.stringify({ channel: 0, state: 'off' }), 'Illum all OFF...');
    }
    const n = parseInt(args[0], 10);
    const state = (args[1] || '').toLowerCase();
    if (!(n >= 1 && n <= 4) || (state !== 'on' && state !== 'off')) {
        return reply('Usage: ILLUM 1-4 ON|OFF or ILLUM OFF');
    }
    return mqttAndReply('illumination/4ch-thyristor/command/set', JSON.stringify({ channel: n, state: state }), 'Illum C' + n + ' ' + state.toUpperCase());
}

if (cmd === 'irrig_status') {
    const z = flow.get('sms_irrig_zones') || {};
    const bits = [];
    for (let i = 1; i <= 12; i++) {
        const key = IRRIG_ZONE_POWER[i];
        bits.push('I' + i + '=' + (z[key] || '?'));
    }
    return reply('Irrig: ' + bits.join(' '));
}
if (cmd === 'irrig_a_start') return mqttAndReply('irrigation/command/area_a', 'ON', 'Irrig Lawn START...');
if (cmd === 'irrig_a_pause') return mqttAndReply('irrigation/command/area_a', 'pause', 'Irrig Lawn PAUSE...');
if (cmd === 'irrig_a_resume') return mqttAndReply('irrigation/command/area_a', 'resume', 'Irrig Lawn RESUME...');
if (cmd === 'irrig_a_skip') return mqttAndReply('irrigation/command/area_a', 'skip', 'Irrig Lawn SKIP...');
if (cmd === 'irrig_b_start') return mqttAndReply('irrigation/command/area_b', 'ON', 'Irrig Flowers START...');
if (cmd === 'irrig_b_pause') return mqttAndReply('irrigation/command/area_b', 'pause', 'Irrig Flowers PAUSE...');
if (cmd === 'irrig_b_resume') return mqttAndReply('irrigation/command/area_b', 'resume', 'Irrig Flowers RESUME...');
if (cmd === 'irrig_b_skip') return mqttAndReply('irrigation/command/area_b', 'skip', 'Irrig Flowers SKIP...');
if (cmd === 'irrig') {
    const n = parseInt(args[0], 10);
    const state = (args[1] || '').toUpperCase();
    if (!(n >= 1 && n <= 12) || (state !== 'ON' && state !== 'OFF')) {
        return reply('Usage: IRRIG 1-12 ON|OFF');
    }
    const power = IRRIG_ZONE_POWER[n];
    return mqttAndReply('cmnd/IrigationSystem/' + power, state, 'Irrig I' + n + ' ' + state);
}

if (cmd === 'pump_start') return mqttAndReply('cmnd/pompaApa/Power1', 'ON', 'Pump START...');
if (cmd === 'pump_stop') return mqttAndReply('cmnd/pompaApa/Power1', 'OFF', 'Pump STOP...');
if (cmd === 'pump_drain') return mqttAndReply('cmnd/pompaApa/Power2', 'ON', 'Drain 10s...');
if (cmd === 'pump_trench1_on') return mqttAndReply('cmnd/pompaApa/Power3', 'ON', 'Trench1 ON...');
if (cmd === 'pump_trench1_off') return mqttAndReply('cmnd/pompaApa/Power3', 'OFF', 'Trench1 OFF...');
if (cmd === 'pump_trench2_on') return mqttAndReply('cmnd/pompaApa/Power4', 'ON', 'Trench2 ON...');
if (cmd === 'pump_trench2_off') return mqttAndReply('cmnd/pompaApa/Power4', 'OFF', 'Trench2 OFF...');
if (cmd === 'pump_status') {
    const p = global.get('water_pump_state') || {};
    return reply('Pump=' + (p.pump_power||'?') + ' Drain=' + (p.drain_water||'?') + ' T1=' + (p.feed_trench_1||'?') + ' T2=' + (p.feed_trench_2||'?'));
}

if (cmd === 'aquarium_on') return mqttAndReply('cmnd/sursaAcvariu/POWER', 'ON', 'Aquarium ON...');
if (cmd === 'aquarium_off') return mqttAndReply('cmnd/sursaAcvariu/POWER', 'OFF', 'Aquarium OFF...');
if (cmd === 'aquarium_toggle') return mqttAndReply('cmnd/sursaAcvariu/POWER', 'TOGGLE', 'Aquarium TOGGLE...');
if (cmd === 'aquarium_status') {
    const a = global.get('aquarium_state') || {};
    return reply('Aquarium: ' + (a.light_power || 'unknown'));
}

if (cmd === 'camera_status') {
    const healthStore = flow.get('camera_health') || {};
    const cameras = Object.keys(healthStore);
    if (!cameras.length) return reply('Cameras: none reporting');
    let text = 'Cameras: ';
    cameras.forEach(name => {
        const health = healthStore[name] || {};
        text += name + '=' + String(health.state || 'unknown').toUpperCase() + '; ';
    });
    return reply(text);
}
if (cmd === 'camera_help') return reply('CAMERA_STATUS health. Alerts on Telegram.');

if (cmd === 'sms_status') {
    const sd = flow.get('sms_gateway_status') || {};
    return reply('SMS GW: WiFi=' + (sd.wifi||'?') + ' MQTT=' + (sd.mqtt||'?') + ' GSM=' + (sd.gsm||'?') + ' fw=' + (sd.fw||'?'));
}
if (cmd === 'sms_log') {
    const log = flow.get('sms_message_log') || [];
    if (!log.length) return reply('No SMS received yet');
    const recent = log.slice(0, 3);
    let text = 'Recent: ';
    recent.forEach((m, i) => {
        text += (i + 1) + '.' + (m.from || '?') + ':' + String(m.text || '').substring(0, 24) + ' ';
    });
    return reply(text);
}

if (cmd === 'energy_status') {
    const energy = global.get('victron_energy_state') || {};
    if (!energy.timestamp) return reply('Victron: no data yet');
    const bat = energy.battery || {};
    const pv = energy.pv || {};
    const load = energy.load || {};
    const auto = energy.automation || {};
    const soc = bat.soc_pct != null ? bat.soc_pct + '%' : '?';
    const pvW = pv.power_w != null ? Math.round(Number(pv.power_w)) : '?';
    const loadW = load.power_w != null ? Math.round(Number(load.power_w)) : '?';
    const hr = auto.headroom_w != null ? Math.round(Number(auto.headroom_w)) : '?';
    return reply('Victron SOC ' + soc + ' PV ' + pvW + 'W Load ' + loadW + 'W Headroom ' + hr + 'W');
}
if (cmd === 'energy_start') {
    const energy = global.get('victron_energy_state') || {};
    const auto = energy.automation || {};
    if (!auto.can_add_load) {
        const hr = auto.headroom_w != null ? Math.round(Number(auto.headroom_w)) : '?';
        return reply('Cannot start load. Headroom ' + hr + 'W');
    }
    const body = JSON.stringify({ action: 'start', source: 'sms', timestamp: new Date().toISOString(), enabled: true });
    return sendMany([
        { topic: 'energy/victron/command/discretionary/start', payload: body },
        { topic: 'energy/victron/automation/discretionary_load/state', payload: body }
    ], 'Discretionary load START...');
}
if (cmd === 'energy_stop') {
    const body = JSON.stringify({ action: 'stop', source: 'sms', timestamp: new Date().toISOString(), enabled: false });
    return sendMany([
        { topic: 'energy/victron/command/discretionary/stop', payload: body },
        { topic: 'energy/victron/automation/discretionary_load/state', payload: body }
    ], 'Discretionary load STOP...');
}

if (cmd === 'huawei_status') {
    const energy = global.get('huawei_energy_state') || {};
    if (!energy.timestamp) return reply('Huawei: no data yet');
    const inv = energy.inverter || {};
    const pv = energy.pv || {};
    const ap = inv.active_power_w != null ? Math.round(Number(inv.active_power_w)) : '?';
    const dc = pv.input_power_w != null ? Math.round(Number(pv.input_power_w)) : '?';
    const day = inv.daily_yield_kwh != null ? inv.daily_yield_kwh : '?';
    return reply('Huawei P=' + ap + 'W DC=' + dc + 'W Day=' + day + 'kWh');
}

if (cmd === 'scala1_status') {
    const s = global.get('grundfos_scala1_state') || {};
    if (!s.timestamp) return reply('SCALA1: no data yet');
    const run = s.running === true ? 'RUN' : (s.running === false ? 'STOP' : '?');
    const bar = s.pressure_bar != null ? Number(s.pressure_bar).toFixed(2) : '?';
    const w = s.power_w != null ? Math.round(Number(s.power_w)) : '?';
    return reply('SCALA1 ' + run + ' ' + bar + 'bar ' + w + 'W');
}
if (cmd === 'scala1_start') return mqttAndReply('water/grundfos/scala1/command', { action: 'start' }, 'SCALA1 start (BLE)...');
if (cmd === 'scala1_stop') return mqttAndReply('water/grundfos/scala1/command', { action: 'stop' }, 'SCALA1 stop (BLE)...');

if (cmd === 'consumer_status') {
    const store = flow.get('sms_consumer_status') || {};
    const ids = ['front-lights-breaker', 'breaker-inside', 'breaker-outside', 'garden-power-hut'];
    const bits = ids.map(id => {
        const p = store[id] || {};
        const st = p.state || p.switch || (p.online === false ? 'offline' : '?');
        return id.replace('breaker-', '').replace('-breaker', '') + '=' + st;
    });
    return reply('Consumers: ' + bits.join(' '));
}
if (cmd === 'consumer') {
    const rawId = args[0] || '';
    const state = (args[1] || '').toLowerCase();
    const id = CONSUMER_IDS[rawId];
    if (!id || (state !== 'on' && state !== 'off')) {
        return reply('Usage: CONSUMER front|inside|outside|hut ON|OFF');
    }
    const body = { action: state, source: 'sms', consumer_id: id };
    return mqttAndReply('energy/consumers/' + id + '/command/switch', body, 'Consumer ' + id + ' ' + state.toUpperCase());
}

return reply('Unknown. Send HELP');
"""

CACHE_ILLUM = r"""let p = msg.payload;
if (Buffer.isBuffer(p)) p = p.toString('utf8');
if (typeof p === 'string') { try { p = JSON.parse(p); } catch (e) { return null; } }
if (p && typeof p === 'object') flow.set('sms_illum_status', p);
return null;"""

CACHE_IRRIG = r"""const topic = msg.topic || '';
const seg = topic.split('/');
const key = seg[seg.length - 1];
if (!key || key.indexOf('POWER') !== 0) return null;
let v = msg.payload;
if (Buffer.isBuffer(v)) v = v.toString('utf8');
if (typeof v === 'object' && v) {
    if (v[key] != null) v = v[key];
    else if (v.POWER != null) v = v.POWER;
}
v = String(v).trim().toUpperCase();
const z = flow.get('sms_irrig_zones') || {};
z[key] = v;
flow.set('sms_irrig_zones', z);
return null;"""

CACHE_CONSUMER = r"""let p = msg.payload;
if (Buffer.isBuffer(p)) p = p.toString('utf8');
if (typeof p === 'string') { try { p = JSON.parse(p); } catch (e) { return null; } }
const topic = msg.topic || '';
const m = topic.match(/^energy\/consumers\/([^/]+)\/status$/);
if (!m || !p) return null;
const store = flow.get('sms_consumer_status') || {};
store[m[1]] = p;
flow.set('sms_consumer_status', store);
return null;"""

IRRIG_BRIDGE = r"""const topic = msg.topic || '';
let p = msg.payload;
if (Buffer.isBuffer(p)) p = p.toString('utf8');
p = String(p).trim();
const area = topic.indexOf('area_b') >= 0 ? 'b' : 'a';
msg.payload = p;
if (p === 'ON') {
    msg.topic = 'topic';
    return area === 'a' ? [msg, null, null, null] : [null, null, msg, null];
}
msg.topic = p;
return area === 'a' ? [null, msg, null, null] : [null, null, null, msg];"""

nodes = [
    {
        "id": "sms_domain_comment",
        "type": "comment",
        "z": "tab_dashboard",
        "name": "═══════════════ SMS DOMAIN GATEWAY (515) ═══════════════",
        "info": "## SMS Domain Gateway\n\n**Flow 515** — handles `sms/command/dispatch`, publishes `sms/command/reply` and device MQTT commands.\nSee docs/SMS_INTERFACE.md.",
        "x": 420,
        "y": 40,
        "wires": [],
    },
    {
        "id": "mqtt_in_sms_dispatch",
        "type": "mqtt in",
        "z": "tab_dashboard",
        "name": "SMS Dispatch (In)",
        "topic": "sms/command/dispatch",
        "qos": "1",
        "datatype": "auto",
        "broker": "mqtt_broker_local",
        "nl": False,
        "rap": True,
        "rh": 0,
        "inputs": 0,
        "x": 140,
        "y": 120,
        "wires": [["func_sms_domain_handler"]],
    },
    {
        "id": "func_sms_domain_handler",
        "type": "function",
        "z": "tab_dashboard",
        "name": "Handle SMS Domains",
        "func": HANDLER,
        "outputs": 1,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": 380,
        "y": 120,
        "wires": [["switch_sms_domain_out"]],
    },
    {
        "id": "switch_sms_domain_out",
        "type": "switch",
        "z": "tab_dashboard",
        "name": "Reply vs device cmd",
        "property": "topic",
        "propertyType": "msg",
        "rules": [
            {"t": "eq", "v": "sms/command/reply", "vt": "str"},
            {"t": "else"},
        ],
        "checkall": "false",
        "repair": False,
        "outputs": 2,
        "x": 620,
        "y": 120,
        "wires": [["mqtt_out_sms_domain_reply"], ["mqtt_out_sms_domain_cmd"]],
    },
    {
        "id": "mqtt_out_sms_domain_reply",
        "type": "mqtt out",
        "z": "tab_dashboard",
        "name": "SMS Reply Bus",
        "topic": "sms/command/reply",
        "qos": "1",
        "retain": "",
        "respTopic": "",
        "contentType": "",
        "userProps": "",
        "correl": "",
        "expiry": "",
        "broker": "mqtt_broker_local",
        "x": 880,
        "y": 80,
        "wires": [],
    },
    {
        "id": "mqtt_out_sms_domain_cmd",
        "type": "mqtt out",
        "z": "tab_dashboard",
        "name": "Device Command",
        "topic": "",
        "qos": "1",
        "retain": "",
        "respTopic": "",
        "contentType": "",
        "userProps": "",
        "correl": "",
        "expiry": "",
        "broker": "mqtt_broker_local",
        "x": 880,
        "y": 160,
        "wires": [],
    },
    {
        "id": "mqtt_in_sms_illum_cache",
        "type": "mqtt in",
        "z": "tab_dashboard",
        "name": "Illum status cache",
        "topic": "illumination/4ch-thyristor/status",
        "qos": "1",
        "datatype": "auto",
        "broker": "mqtt_broker_local",
        "nl": False,
        "rap": True,
        "rh": 0,
        "inputs": 0,
        "x": 150,
        "y": 260,
        "wires": [["func_sms_illum_cache"]],
    },
    {
        "id": "func_sms_illum_cache",
        "type": "function",
        "z": "tab_dashboard",
        "name": "Cache illum status",
        "func": CACHE_ILLUM,
        "outputs": 1,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": 400,
        "y": 260,
        "wires": [[]],
    },
    {
        "id": "mqtt_in_sms_irrig_cache",
        "type": "mqtt in",
        "z": "tab_dashboard",
        "name": "Irrig zone cache",
        "topic": "stat/IrigationSystem/#",
        "qos": "1",
        "datatype": "auto",
        "broker": "mqtt_broker_local",
        "nl": False,
        "rap": True,
        "rh": 0,
        "inputs": 0,
        "x": 140,
        "y": 320,
        "wires": [["func_sms_irrig_cache"]],
    },
    {
        "id": "func_sms_irrig_cache",
        "type": "function",
        "z": "tab_dashboard",
        "name": "Cache irrig zones",
        "func": CACHE_IRRIG,
        "outputs": 1,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": 400,
        "y": 320,
        "wires": [[]],
    },
    {
        "id": "mqtt_in_sms_consumer_cache",
        "type": "mqtt in",
        "z": "tab_dashboard",
        "name": "Consumer status cache",
        "topic": "energy/consumers/+/status",
        "qos": "1",
        "datatype": "auto",
        "broker": "mqtt_broker_local",
        "nl": False,
        "rap": True,
        "rh": 0,
        "inputs": 0,
        "x": 160,
        "y": 380,
        "wires": [["func_sms_consumer_cache"]],
    },
    {
        "id": "func_sms_consumer_cache",
        "type": "function",
        "z": "tab_dashboard",
        "name": "Cache consumer status",
        "func": CACHE_CONSUMER,
        "outputs": 1,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": 420,
        "y": 380,
        "wires": [[]],
    },
    {
        "id": "sms_irrig_bridge_comment",
        "type": "comment",
        "z": "b3b5bbeab11d67eb",
        "name": "SMS irrigation program bridge (515)",
        "info": "MQTT irrigation/command/area_a|b -> Lawn/Flowers run-gate and timerctl",
        "x": 200,
        "y": 4520,
        "wires": [],
    },
    {
        "id": "mqtt_in_sms_irrig_area_a",
        "type": "mqtt in",
        "z": "b3b5bbeab11d67eb",
        "name": "SMS irrig area A",
        "topic": "irrigation/command/area_a",
        "qos": "1",
        "datatype": "auto",
        "broker": "mqtt_broker_local",
        "nl": False,
        "rap": True,
        "rh": 0,
        "inputs": 0,
        "x": 160,
        "y": 4580,
        "wires": [["func_sms_irrig_program_bridge"]],
    },
    {
        "id": "mqtt_in_sms_irrig_area_b",
        "type": "mqtt in",
        "z": "b3b5bbeab11d67eb",
        "name": "SMS irrig area B",
        "topic": "irrigation/command/area_b",
        "qos": "1",
        "datatype": "auto",
        "broker": "mqtt_broker_local",
        "nl": False,
        "rap": True,
        "rh": 0,
        "inputs": 0,
        "x": 160,
        "y": 4640,
        "wires": [["func_sms_irrig_program_bridge"]],
    },
    {
        "id": "func_sms_irrig_program_bridge",
        "type": "function",
        "z": "b3b5bbeab11d67eb",
        "name": "Route SMS irrig program",
        "func": IRRIG_BRIDGE,
        "outputs": 4,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": 420,
        "y": 4610,
        "wires": [
            ["c51a5cdc8046bb29"],
            ["33780971f401840a"],
            ["a1b2c3d4e5f67890"],
            ["e7f8a9b0c1d2e3f4"],
        ],
    },
]

root = Path(__file__).resolve().parents[2]
out = root / "flows" / "515-sms-domain-gateway.json"
out.write_text(json.dumps(nodes, indent=4) + "\n", encoding="utf-8")
print(f"wrote {out} nodes={len(nodes)} handler_chars={len(HANDLER)}")


if __name__ == "__main__":
    pass
