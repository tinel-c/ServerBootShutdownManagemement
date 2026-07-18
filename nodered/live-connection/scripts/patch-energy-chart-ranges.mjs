/**
 * Add 1h / 1d / 7d chart ranges to Victron 811 and Huawei 821.
 * - Backend: 1-minute buckets for last 24h (day_chart)
 * - Frontend: range tabs + filtered views
 */
import { readFileSync, writeFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const flowsDir = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "flows");

const DAY_HISTORY_SNIPPET_VICTRON = `
const DAY_MS = 24 * 60 * 60 * 1000;
const FINE_BUCKET_MS = 60 * 1000;
let dayHist = flow.get('victron_day_history') || [];
const fineBucket = Math.floor(reportMs / FINE_BUCKET_MS) * FINE_BUCKET_MS;
if (dayHist.length && dayHist[dayHist.length - 1].bucket === fineBucket) {
    dayHist[dayHist.length - 1] = { bucket: fineBucket, ...point };
} else {
    dayHist.push({ bucket: fineBucket, ...point });
}
const dayCutoff = Date.now() - DAY_MS;
dayHist = dayHist.filter(h => h.t >= dayCutoff);
flow.set('victron_day_history', dayHist);
data.day_chart = dayHist;`;

const DAY_HISTORY_SNIPPET_HUAWEI = `
const DAY_MS = 24 * 60 * 60 * 1000;
const FINE_BUCKET_MS = 60 * 1000;
let dayHist = flow.get('huawei_day_history') || [];
const fineBucket = Math.floor(reportMs / FINE_BUCKET_MS) * FINE_BUCKET_MS;
if (dayHist.length && dayHist[dayHist.length - 1].bucket === fineBucket) {
    dayHist[dayHist.length - 1] = { bucket: fineBucket, ...point };
} else {
    dayHist.push({ bucket: fineBucket, ...point });
}
const dayCutoff = Date.now() - DAY_MS;
dayHist = dayHist.filter(h => h.t >= dayCutoff);
flow.set('huawei_day_history', dayHist);
data.day_chart = dayHist;`;

function addDayHistory(func, snippet) {
  if (func.includes("data.day_chart")) return func;
  const anchor = "data.week_chart = hist;";
  if (!func.includes(anchor)) throw new Error("week_chart anchor not found");
  return func.replace(anchor, `data.week_chart = hist;${snippet}`);
}

function addDayChartToPayloads(func, historyKey) {
  let out = func;
  const dayKey = historyKey.replace("week", "day");
  const weekRef = `week_chart: flow.get('${historyKey}')`;
  if (!out.includes("day_chart:")) {
    out = out.replaceAll(
      weekRef,
      `week_chart: flow.get('${historyKey}'), day_chart: flow.get('${dayKey}') || []`
    );
    out = out.replaceAll(
      `week_chart: hist`,
      `week_chart: hist, day_chart: flow.get('${dayKey}') || []`
    );
    out = out.replace(
      `data.week_chart = flow.get('${historyKey}') || [];`,
      `data.week_chart = flow.get('${historyKey}') || [];\ndata.day_chart = flow.get('${dayKey}') || [];`
    );
    out = out.replace(
      `const data = { ...last, week_chart: hist };`,
      `const data = { ...last, week_chart: hist, day_chart: flow.get('${dayKey}') || [] };`
    );
  }
  return out;
}

const RANGE_BTN_CSS = `
.ec-range-btn {
  appearance: none;
  -webkit-appearance: none;
  border: 1px solid rgba(255,255,255,0.14);
  background: rgba(255,255,255,0.06);
  color: #94a3b8;
  border-radius: 8px;
  padding: 4px 10px;
  font-size: 0.68rem;
  font-weight: 700;
  cursor: pointer;
  line-height: 1.2;
}
.ec-range-btn.active {
  color: #f8fafc;
  border-color: rgba(255,255,255,0.28);
  background: rgba(255,255,255,0.14);
}`;

const CHART_RANGE_METHODS = `
    setChartRange(key) { this.chartRange = key; this.chartHover = null; },
    chartRangeBtnStyle(key) {
      const on = this.chartRange === key;
      return {
        border: '1px solid ' + (on ? 'rgba(255,255,255,0.28)' : 'rgba(255,255,255,0.14)'),
        background: on ? 'rgba(255,255,255,0.14)' : 'rgba(255,255,255,0.06)',
        color: on ? '#f8fafc' : '#94a3b8',
        borderRadius: '8px',
        padding: '4px 10px',
        fontSize: '0.68rem',
        fontWeight: '700',
        cursor: 'pointer'
      };
    },
    chartHoverToleranceMs() {
      if (this.chartRange === '1h') return 90 * 1000;
      if (this.chartRange === '1d') return 3 * 60 * 1000;
      return 45 * 60 * 1000;
    },`;

const CHART_RANGE_COMPUTED = `
    chartRanges() {
      return [
        { key: '1h', label: '1 hour' },
        { key: '1d', label: '24 hours' },
        { key: '7d', label: '7 days' }
      ];
    },
    dayChart() { return this.p.day_chart || []; },
    activeChart() {
      void this.now;
      const now = this.now;
      if (this.chartRange === '1h' || this.chartRange === '1d') {
        const span = this.chartRange === '1h' ? 3600000 : 86400000;
        return (this.dayChart || []).filter(p => p.t >= now - span);
      }
      const span = 7 * 86400000;
      return (this.weekChart || []).filter(p => p.t >= now - span);
    },
    chartRangeLabel() {
      const r = this.chartRanges.find(x => x.key === this.chartRange);
      return r ? r.label : '7 days';
    },
    chartBucketNote() {
      return (this.chartRange === '1h' || this.chartRange === '1d') ? '1 min buckets' : '15 min buckets';
    },`;

function patchChartHelpers(format) {
  let out = format;
  out = out.replace(
    /data\(\) \{ return \{ now: Date\.now\(\), timer: null, chartHover: null \}; \},/,
    "data() { return { now: Date.now(), timer: null, chartHover: null, chartRange: '7d' }; },"
  );
  if (!out.includes("setChartRange(key)")) {
    out = out.replace("methods: {", `methods: {${CHART_RANGE_METHODS}`);
  }
  if (!out.includes("activeChart()")) {
    out = out.replace("weekChart() { return this.p.week_chart || []; },", `weekChart() { return this.p.week_chart || []; },${CHART_RANGE_COMPUTED}`);
  }
  out = out.replaceAll("const pts = this.weekChart;", "const pts = this.activeChart;");
  out = out.replaceAll("this.weekChart.forEach", "this.activeChart.forEach");
  out = out.replaceAll("      const pts = this.weekChart;", "      const pts = this.activeChart;");
  out = out.replace(
    /chartWindow\(\) \{\s*void this\.now;\s*const WEEK = 7 \* 86400000;\s*const t1 = this\.now;\s*return \{ t0: t1 - WEEK, t1, span: WEEK \};\s*\},/,
    `chartWindow() {
      void this.now;
      const spans = { '7d': 7 * 86400000, '1d': 86400000, '1h': 3600000 };
      const span = spans[this.chartRange] || spans['7d'];
      const t1 = this.now;
      return { t0: t1 - span, t1, span };
    },`
  );
  out = out.replace(
    "if (bestD > 45 * 60 * 1000) { this.chartHover = null; return; }",
    "if (bestD > this.chartHoverToleranceMs()) { this.chartHover = null; return; }"
  );
  out = out.replace(
    /chartXTicks\(\) \{\s*void this\.now;\s*const w = this\.chartWindow;\s*const ticks = \[\];\s*const d = new Date\(w\.t0\);\s*d\.setHours\(0, 0, 0, 0\);\s*while \(d\.getTime\(\) <= w\.t1\) \{\s*const t = d\.getTime\(\);\s*if \(t >= w\.t0\) \{\s*ticks\.push\(\{\s*x: this\.chartX\(t\),\s*label: d\.toLocaleDateString\(undefined, \{ weekday: 'short', day: 'numeric' \}\)\s*\}\);\s*\}\s*d\.setDate\(d\.getDate\(\) \+ 1\);\s*\}\s*return ticks;\s*\}/,
    `chartXTicks() {
      void this.now;
      const w = this.chartWindow;
      const ticks = [];
      if (this.chartRange === '1h') {
        const step = 10 * 60 * 1000;
        let t = Math.ceil(w.t0 / step) * step;
        while (t <= w.t1) {
          const d = new Date(t);
          ticks.push({
            x: this.chartX(t),
            label: d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })
          });
          t += step;
        }
        return ticks;
      }
      if (this.chartRange === '1d') {
        const step = 3 * 60 * 60 * 1000;
        let t = Math.ceil(w.t0 / step) * step;
        while (t <= w.t1) {
          const d = new Date(t);
          ticks.push({
            x: this.chartX(t),
            label: d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })
          });
          t += step;
        }
        return ticks;
      }
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
    }`
  );
  return out;
}

function patchVictronChartHtml(format) {
  const rangeHeader = `    <div style="display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between;margin-bottom:10px;">
      <div style="display:flex;flex-wrap:wrap;gap:10px;align-items:center;">
        <div style="font-weight:700;color:#5eead4;">{{ chartRangeLabel }} · {{ chartBucketNote }}</div>
        <div style="display:flex;gap:4px;">
          <button v-for="r in chartRanges" :key="r.key" type="button" :style="chartRangeBtnStyle(r.key)" @click="setChartRange(r.key)">{{ r.label }}</button>
        </div>
      </div>
      <div style="display:flex;flex-wrap:wrap;gap:10px;font-size:0.72em;color:#94a3b8;">
        <span v-for="s in chartLegend" :key="s.key"><span :style="{display:'inline-block',width:'8px',height:'8px',borderRadius:'50%',background:s.color,marginRight:'4px'}"></span>{{ s.label }}</span>
      </div>
    </div>`;

  let out = format.replace(
    /    <div style="display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between;margin-bottom:10px;">\s*<div style="font-weight:700;color:#5eead4;">7-day history \(15 min buckets\)<\/div>\s*<div style="display:flex;flex-wrap:wrap;gap:10px;font-size:0\.72em;color:#94a3b8;">[\s\S]*?<\/div>\s*<\/div>/,
    rangeHeader
  );

  out = out.replace(
    "Hover chart for values · fixed 7-day window · {{ weekChart.length }} samples",
    "Hover chart for values · {{ activeChart.length }} samples"
  );

  if (!out.includes(RANGE_BTN_CSS.trim())) {
    out = out.replace("</style>\n<script>", `${RANGE_BTN_CSS}\n</style>\n<script>`);
  }
  return out;
}

function patchHuaweiChartHtml(format) {
  const rangeHeader = `    <div style="display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between;margin-bottom:10px;">
      <div style="display:flex;flex-wrap:wrap;gap:10px;align-items:center;">
        <div style="font-weight:700;color:#fb923c;">{{ chartRangeLabel }} · {{ chartBucketNote }}</div>
        <div style="display:flex;gap:4px;">
          <button v-for="r in chartRanges" :key="r.key" type="button" :style="chartRangeBtnStyle(r.key)" @click="setChartRange(r.key)">{{ r.label }}</button>
        </div>
      </div>
    </div>`;

  let out = format.replace(
    /<div style="font-weight:700;color:#fb923c;margin-bottom:10px;">7-day active power \(15 min buckets\)<\/div>/,
    rangeHeader
  );

  out = out.replace(
    "Hover chart for values · {{ weekChart.length }} samples",
    "Hover chart for values · {{ activeChart.length }} samples"
  );

  if (!out.includes("chartRangeBtnStyle")) {
    out = out.replace("</style>\n<script>", `${RANGE_BTN_CSS}\n</style>\n<script>`);
  }
  return out;
}

function patchFlow811(data) {
  for (const node of data) {
    if (node.type !== "function" || !node.func) continue;
    if (node.id === "func_victron_process_status") {
      node.func = addDayHistory(node.func, DAY_HISTORY_SNIPPET_VICTRON);
    }
    if (node.func.includes("victron_week_history")) {
      node.func = addDayChartToPayloads(node.func, "victron_week_history");
    }
  }
  const tpl = data.find((n) => n.id === "template_victron_energy_dashboard");
  tpl.format = patchVictronChartHtml(patchChartHelpers(tpl.format));
}

function patchFlow821(data) {
  for (const node of data) {
    if (node.type !== "function" || !node.func) continue;
    if (node.id === "func_huawei_process_status") {
      node.func = addDayHistory(node.func, DAY_HISTORY_SNIPPET_HUAWEI);
    }
    if (node.func.includes("huawei_week_history")) {
      node.func = addDayChartToPayloads(node.func, "huawei_week_history");
    }
  }
  const tpl = data.find((n) => n.id === "template_huawei_energy_dashboard");
  tpl.format = patchHuaweiChartHtml(patchChartHelpers(tpl.format));
}

for (const [file, patchFn] of [
  ["811-victron-energy-status.json", patchFlow811],
  ["821-huawei-energy-status.json", patchFlow821],
]) {
  const path = join(flowsDir, file);
  const data = JSON.parse(readFileSync(path, "utf8"));
  patchFn(data);
  writeFileSync(path, `${JSON.stringify(data, null, 4)}\n`);
  console.log(`Patched ${file}`);
}
