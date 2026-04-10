# -*- coding: utf-8 -*-
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
path421 = os.path.join(BASE, "421-irrigation-status-dashboard.json")

with open(os.path.join(BASE, "_irr421_merge_func.js"), encoding="utf-8") as f:
    merge_func = f.read()

with open(os.path.join(BASE, "_irr421_openmeteo.js"), encoding="utf-8") as f:
    openmeteo_func = f.read()

with open(os.path.join(BASE, "_irr421_scheduler.js"), encoding="utf-8") as f:
    sched_func = f.read()

INIT_MERGE = """if (flow.get('irrigation_sched_area_a_hour') == null) flow.set('irrigation_sched_area_a_hour', 3);
if (flow.get('irrigation_sched_area_a_minute') == null) flow.set('irrigation_sched_area_a_minute', 0);
if (flow.get('irrigation_sched_area_b_hour') == null) flow.set('irrigation_sched_area_b_hour', 5);
if (flow.get('irrigation_sched_area_b_minute') == null) flow.set('irrigation_sched_area_b_minute', 0);
if (flow.get('irrigation_rain_skip_mm') == null) flow.set('irrigation_rain_skip_mm', 1);
if (flow.get('irrigation_rain_skip_prob') == null) flow.set('irrigation_rain_skip_prob', 70);
if (flow.get('irrigation_lat') == null) flow.set('irrigation_lat', 47.0966);
if (flow.get('irrigation_lon') == null) flow.set('irrigation_lon', 27.5632);
if (flow.get('irrigation_location_name') == null) flow.set('irrigation_location_name', 'Lunca Cetățuii, Iași, RO');
"""

with open(path421, encoding="utf-8") as f:
    data = json.load(f)

nodes = {n["id"]: n for n in data}

nodes["irr421_func_merge"]["func"] = merge_func
nodes["irr421_func_merge"]["initialize"] = INIT_MERGE

# init inject -> merge + openmeteo
nodes["irr421_inject_init"]["wires"] = [["irr421_func_merge", "irr421_func_openmeteo_fetch"]]

new_nodes = [
    {
        "id": "irr421_link_out_sched_lawn",
        "type": "link out",
        "z": "tab_dashboard",
        "name": "→ Start Lawn (420)",
        "mode": "link",
        "links": ["irr420_link_in_sched_lawn"],
        "x": 560,
        "y": 520,
        "wires": [],
    },
    {
        "id": "irr421_inject_weather_6h",
        "type": "inject",
        "z": "tab_dashboard",
        "name": "Weather every 6h",
        "props": [{"p": "payload"}],
        "repeat": "21600",
        "crontab": "",
        "once": True,
        "onceDelay": 1.5,
        "topic": "",
        "payload": "",
        "payloadType": "date",
        "x": 140,
        "y": 460,
        "wires": [["irr421_func_openmeteo_fetch"]],
    },
    {
        "id": "irr421_func_openmeteo_fetch",
        "type": "function",
        "z": "tab_dashboard",
        "name": "Fetch Open-Meteo",
        "func": openmeteo_func,
        "outputs": 1,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": 300,
        "y": 460,
        "wires": [["irr421_func_merge"]],
    },
    {
        "id": "irr421_inject_minute_sched",
        "type": "inject",
        "z": "tab_dashboard",
        "name": "Scheduler tick 60s",
        "props": [{"p": "payload"}],
        "repeat": "60",
        "crontab": "",
        "once": False,
        "onceDelay": 0.5,
        "topic": "",
        "payload": "",
        "payloadType": "str",
        "x": 140,
        "y": 560,
        "wires": [["irr421_func_scheduler"]],
    },
    {
        "id": "irr421_func_scheduler",
        "type": "function",
        "z": "tab_dashboard",
        "name": "Daily irrigation scheduler",
        "func": sched_func,
        "outputs": 1,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": 300,
        "y": 560,
        "wires": [["irr421_link_out_sched_lawn"]],
    },
]

# Rebuild data: insert new nodes before last element (or append)
idx_ui = next(i for i, n in enumerate(data) if n["id"] == "irr421_ui_template")
for nn in new_nodes:
    if not any(x["id"] == nn["id"] for x in data):
        data.insert(idx_ui, nn)

# Template format prepend
WEATHER_INJECT = r'''  <div v-if="msg.payload.weatherUi" style="margin-bottom: 16px;">
    <div style="display: flex; align-items: flex-start; justify-content: space-between; flex-wrap: wrap; gap: 10px; margin-bottom: 10px;">
      <div>
        <div style="font-weight: 700; font-size: 0.95rem; color: #e0f2fe; letter-spacing: 0.03em;">7-day forecast</div>
        <div style="font-size: 0.68rem; color: #64748b; margin-top: 4px; max-width: 520px; line-height: 1.4;">
          {{ msg.payload.weatherUi.sourceName }} · Last fetch: {{ fmtWeatherTime(msg.payload.weatherUi.fetchedAt) }}
          <span v-if="msg.payload.weatherUi.lat != null"> · {{ msg.payload.weatherUi.lat.toFixed(2) }}, {{ msg.payload.weatherUi.lon.toFixed(2) }}</span>
          <br/><a :href="msg.payload.weatherUi.detailUrl" target="_blank" rel="noopener noreferrer" style="color: #7dd3fc;">{{ msg.payload.weatherUi.attribution }}</a>
        </div>
      </div>
    </div>
    <div v-if="msg.payload.weatherUi.hasData" style="display: flex; gap: 8px; overflow-x: auto; padding-bottom: 6px; scrollbar-width: thin;">
      <div v-for="(d, i) in msg.payload.weatherUi.days" :key="'wx'+i" :style="wxDayStyle(d)" style="flex: 0 0 92px; border-radius: 12px; padding: 10px 8px; text-align: center; border: 1px solid rgba(255,255,255,0.1);">
        <div style="font-size: 0.65rem; color: #94a3b8; text-transform: uppercase;">{{ d.dayShort }}</div>
        <div style="font-size: 1.35rem; margin: 4px 0;">{{ d.icon }}</div>
        <div style="font-size: 0.72rem; color: #e2e8f0; font-weight: 600;">{{ d.tmax }}° / {{ d.tmin }}°</div>
        <div style="font-size: 0.62rem; color: #7dd3fc; margin-top: 4px;">{{ d.precipMm }} mm</div>
        <div style="font-size: 0.58rem; color: #94a3b8;">{{ d.precipProb }}% rain</div>
        <div style="height: 4px; border-radius: 2px; background: rgba(0,0,0,0.35); margin-top: 6px; overflow: hidden;">
          <div :style="{ height: '100%', width: d.barPct + '%', background: d.wet ? 'linear-gradient(90deg,#38bdf8,#0ea5e9)' : 'rgba(148,163,184,0.4)' }"></div>
        </div>
        <div v-if="d.wet" style="font-size: 0.58rem; color: #fbbf24; margin-top: 4px;">Wet</div>
      </div>
    </div>
    <div v-else style="font-size: 0.75rem; color: #64748b; padding: 8px;">Loading weather… deploy & wait for first fetch.</div>
  </div>

  <div v-if="msg.payload.scheduleUi" style="margin-bottom: 16px; display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
    <div style="background: linear-gradient(135deg, rgba(14,165,233,0.25), rgba(30,27,75,0.5)); border-radius: 14px; padding: 12px; border: 1px solid rgba(125,211,252,0.25);">
      <div style="font-size: 0.72rem; font-weight: 700; color: #bae6fd; text-transform: uppercase; letter-spacing: 0.06em;">Area A — next run</div>
      <div style="font-size: 1.1rem; font-weight: 700; color: #f0f9ff; margin-top: 6px;">{{ msg.payload.scheduleUi.countdownA }}</div>
      <div style="font-size: 0.68rem; color: #94a3b8; margin-top: 4px;">{{ msg.payload.scheduleUi.labelA }}</div>
      <div style="font-size: 0.65rem; color: #64748b; margin-top: 6px;">Default local time {{ pad2(msg.payload.scheduleUi.areaAHour) }}:{{ pad2(msg.payload.scheduleUi.areaAMin) }} · skip if rain ≥ {{ msg.payload.scheduleUi.rainSkipMm }} mm or prob ≥ {{ msg.payload.scheduleUi.rainSkipProb }}%</div>
    </div>
    <div style="background: linear-gradient(135deg, rgba(99,102,241,0.25), rgba(30,27,75,0.5)); border-radius: 14px; padding: 12px; border: 1px solid rgba(165,180,252,0.25);">
      <div style="font-size: 0.72rem; font-weight: 700; color: #c7d2fe; text-transform: uppercase; letter-spacing: 0.06em;">Area B — next run</div>
      <div style="font-size: 1.1rem; font-weight: 700; color: #f5f3ff; margin-top: 6px;">{{ msg.payload.scheduleUi.countdownB }}</div>
      <div style="font-size: 0.68rem; color: #94a3b8; margin-top: 4px;">{{ msg.payload.scheduleUi.labelB }}</div>
      <div style="font-size: 0.65rem; color: #64748b; margin-top: 6px;">Default local time {{ pad2(msg.payload.scheduleUi.areaBHour) }}:{{ pad2(msg.payload.scheduleUi.areaBMin) }}</div>
    </div>
  </div>
  <div style="font-size: 0.65rem; color: #475569; margin: -8px 0 12px 4px;">{{ msg.payload.scheduleUi.note }}</div>

'''

tpl = nodes["irr421_ui_template"]["format"]
needle = '<div v-if="msg.payload" style="font-family: system-ui, -apple-system, \'Segoe UI\', sans-serif;'
if WEATHER_INJECT.strip() not in tpl:
    if needle in tpl:
        tpl = tpl.replace(needle, needle + "\n" + WEATHER_INJECT, 1)
    else:
        raise SystemExit("template needle not found")
nodes["irr421_ui_template"]["format"] = tpl

# Add Vue methods: fmtWeatherTime, wxDayStyle, pad2
script_needle = "export default {\n  methods: {"
if script_needle in tpl and "fmtWeatherTime" not in tpl:
    tpl = nodes["irr421_ui_template"]["format"]
    tpl = tpl.replace(
        script_needle,
        script_needle + "\n    pad2(n) {\n      const x = Number(n) || 0;\n      return x < 10 ? '0' + x : String(x);\n    },\n    fmtWeatherTime(iso) {\n      if (!iso) return '—';\n      try { return new Date(iso).toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'medium' }); } catch (e) { return iso; }\n    },\n    wxDayStyle(d) {\n      return d && d.wet ? { background: 'rgba(30,58,138,0.35)' } : { background: 'rgba(255,255,255,0.06)' };\n    },",
        1,
    )
    nodes["irr421_ui_template"]["format"] = tpl

# Comment
nodes["irr421_comment_0001"]["info"] = (
    nodes["irr421_comment_0001"]["info"]
    + "\n\n### Weather (Open-Meteo)\n"
    + "- Fetches **4×/day** (every **6 h**).\n"
    + "- Set **`flow.irrigation_lat`** / **`flow.irrigation_lon`** / **`flow.irrigation_location_name`** (defaults: Lunca Cetățuii, Iași).\n"
    + "- **Rain skip**: `flow.irrigation_rain_skip_mm` (default 1), `flow.irrigation_rain_skip_prob` (default 70).\n\n"
    + "### Scheduler\n"
    + "- **Area A** default **03:00**, **Area B** default **05:00** local (Node-RED host time).\n"
    + "- `flow.irrigation_sched_area_a_hour` / `_minute`, same for B.\n"
    + "- `flow.irrigation_scheduler_enabled` = `false` to disable.\n"
    + "- Triggers **Lawn** `run-gate` via **link** to flow **420** (same as **Start** buttons).\n"
)

with open(path421, "w", encoding="utf-8", newline="\n") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)
    f.write("\n")

print("patched", path421)
