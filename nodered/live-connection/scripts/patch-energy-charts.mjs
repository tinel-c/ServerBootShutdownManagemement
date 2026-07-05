import { readFileSync, writeFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const flowsDir = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "flows");

const CHART_HELPERS = `
    onChartLeave() { this.chartHover = null; },
    onChartMove(evt) {
      const svg = evt.currentTarget;
      const rect = svg.getBoundingClientRect();
      if (!rect.width) return;
      const x = ((evt.clientX - rect.left) / rect.width) * 800;
      if (x < 10 || x > 790) { this.chartHover = null; return; }
      const w = this.chartWindow;
      const t = w.t0 + ((x - 10) / 780) * w.span;
      const pts = this.weekChart;
      if (!pts.length) { this.chartHover = null; return; }
      let best = pts[0];
      let bestD = Math.abs(best.t - t);
      for (let i = 1; i < pts.length; i++) {
        const d = Math.abs(pts[i].t - t);
        if (d < bestD) { bestD = d; best = pts[i]; }
      }
      if (bestD > 45 * 60 * 1000) { this.chartHover = null; return; }
      const px = evt.clientX - rect.left;
      this.chartHover = this.buildChartHover(best, px);
    },`;

const VICTRON_CHART_BLOCK = `  <div v-if="weekChart.length" class="energy-chart-wrap" style="margin-top:16px;margin-bottom:8px;padding:14px;border-radius:14px;background:rgba(0,0,0,0.28);border:1px solid rgba(94,234,212,0.2);">
    <div style="display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between;margin-bottom:10px;">
      <div style="font-weight:700;color:#5eead4;">7-day history (15 min buckets)</div>
      <div style="display:flex;flex-wrap:wrap;gap:10px;font-size:0.72em;color:#94a3b8;">
        <span v-for="s in chartLegend" :key="s.key"><span :style="{display:'inline-block',width:'8px',height:'8px',borderRadius:'50%',background:s.color,marginRight:'4px'}"></span>{{ s.label }}</span>
      </div>
    </div>
    <div style="position:relative;" @mouseleave="onChartLeave">
      <svg viewBox="0 0 800 260" style="width:100%;height:auto;display:block;" @mousemove="onChartMove">
        <text x="12" y="18" fill="#94a3b8" font-size="10" font-weight="600">{{ chartPowerMax }} W</text>
        <text x="12" y="120" fill="#64748b" font-size="10" font-weight="600">0 W</text>
        <text x="12" y="214" fill="#94a3b8" font-size="10" font-weight="600">SoC 100%</text>
        <text x="12" y="226" fill="#64748b" font-size="10" font-weight="600">0%</text>
        <line x1="10" y1="115" x2="790" y2="115" stroke="rgba(255,255,255,0.18)" stroke-width="0.8" stroke-dasharray="3 3"/>
        <line x1="10" y1="28" x2="790" y2="28" stroke="rgba(255,255,255,0.06)" stroke-width="0.6"/>
        <line x1="10" y1="218" x2="790" y2="218" stroke="rgba(255,255,255,0.06)" stroke-width="0.6"/>
        <g v-for="(tick,i) in chartXTicks" :key="'x'+i">
          <line :x1="tick.x" y1="12" :x2="tick.x" y2="218" stroke="rgba(255,255,255,0.06)" stroke-width="0.6"/>
          <text :x="tick.x" y="248" fill="#94a3b8" font-size="10" font-weight="600" text-anchor="middle">{{ tick.label }}</text>
        </g>
        <line v-if="chartHover" :x1="chartHover.x" y1="12" :x2="chartHover.x" y2="218" stroke="rgba(255,255,255,0.35)" stroke-width="0.8"/>
        <path v-for="line in chartLines" :key="line.key" :d="line.path" fill="none" :stroke="line.color" stroke-width="1.1" stroke-linejoin="round" stroke-linecap="round" :opacity="chartHover ? (chartHover.activeKey === line.key ? 1 : 0.28) : 0.92"/>
        <circle v-if="chartHover && chartHover.dot" :cx="chartHover.dot.x" :cy="chartHover.dot.y" r="3.5" :fill="chartHover.dot.color" stroke="#0f172a" stroke-width="1"/>
      </svg>
      <div v-if="chartHover" class="energy-chart-tooltip" :style="{ left: chartHover.px + 'px' }">
        <div class="energy-chart-tooltip-time">{{ chartHover.timeLabel }}</div>
        <div v-for="row in chartHover.rows" :key="row.key" class="energy-chart-tooltip-row">
          <span class="energy-chart-tooltip-dot" :style="{ background: row.color }"></span>
          <span>{{ row.label }}</span>
          <strong>{{ row.value }}</strong>
        </div>
      </div>
    </div>
    <div style="font-size:0.72em;color:#64748b;margin-top:6px;">Hover chart for values · fixed 7-day window · {{ weekChart.length }} samples</div>
  </div>`;

const HUAWEI_CHART_BLOCK = `  <div v-if="weekChart.length" class="energy-chart-wrap" style="margin-top:8px;padding:14px;border-radius:14px;background:rgba(0,0,0,0.28);border:1px solid rgba(251,146,60,0.25);">
    <div style="font-weight:700;color:#fb923c;margin-bottom:10px;">7-day active power (15 min buckets)</div>
    <div style="position:relative;" @mouseleave="onChartLeave">
      <svg viewBox="0 0 800 200" style="width:100%;height:auto;display:block;" @mousemove="onChartMove">
        <text x="12" y="16" fill="#94a3b8" font-size="10" font-weight="600">{{ chartPowerMax }} W</text>
        <text x="12" y="104" fill="#64748b" font-size="10" font-weight="600">0 W</text>
        <line x1="10" y1="100" x2="790" y2="100" stroke="rgba(255,255,255,0.18)" stroke-width="0.8" stroke-dasharray="3 3"/>
        <line x1="10" y1="24" x2="790" y2="24" stroke="rgba(255,255,255,0.06)" stroke-width="0.6"/>
        <line x1="10" y1="176" x2="790" y2="176" stroke="rgba(255,255,255,0.06)" stroke-width="0.6"/>
        <g v-for="(tick,i) in chartXTicks" :key="'x'+i">
          <line :x1="tick.x" y1="12" :x2="tick.x" y2="180" stroke="rgba(255,255,255,0.06)" stroke-width="0.6"/>
          <text :x="tick.x" y="196" fill="#94a3b8" font-size="10" font-weight="600" text-anchor="middle">{{ tick.label }}</text>
        </g>
        <line v-if="chartHover" :x1="chartHover.x" y1="12" :x2="chartHover.x" y2="180" stroke="rgba(255,255,255,0.35)" stroke-width="0.8"/>
        <path :d="powerPath" fill="none" stroke="#fb923c" stroke-width="1.1" stroke-linejoin="round" stroke-linecap="round" :opacity="chartHover ? 1 : 0.92"/>
        <circle v-if="chartHover && chartHover.dot" :cx="chartHover.dot.x" :cy="chartHover.dot.y" r="3.5" fill="#fb923c" stroke="#0f172a" stroke-width="1"/>
      </svg>
      <div v-if="chartHover" class="energy-chart-tooltip" :style="{ left: chartHover.px + 'px' }">
        <div class="energy-chart-tooltip-time">{{ chartHover.timeLabel }}</div>
        <div class="energy-chart-tooltip-row">
          <span class="energy-chart-tooltip-dot" style="background:#fb923c"></span>
          <span>Active power</span>
          <strong>{{ chartHover.value }}</strong>
        </div>
      </div>
    </div>
    <div style="font-size:0.72em;color:#64748b;margin-top:6px;">Hover chart for values · {{ weekChart.length }} samples</div>
  </div>`;

const CHART_CSS = `
<style>
.energy-chart-wrap .energy-chart-tooltip {
  position: absolute;
  top: 8px;
  transform: translateX(-50%);
  min-width: 148px;
  max-width: 220px;
  padding: 8px 10px;
  border-radius: 8px;
  background: rgba(15, 23, 42, 0.94);
  border: 1px solid rgba(255, 255, 255, 0.14);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45);
  pointer-events: none;
  z-index: 5;
  font-size: 0.72rem;
  color: #e2e8f0;
}
.energy-chart-wrap .energy-chart-tooltip-time {
  font-weight: 700;
  color: #f8fafc;
  margin-bottom: 6px;
  font-size: 0.68rem;
}
.energy-chart-wrap .energy-chart-tooltip-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 3px;
}
.energy-chart-wrap .energy-chart-tooltip-row strong {
  margin-left: auto;
  font-variant-numeric: tabular-nums;
}
.energy-chart-wrap .energy-chart-tooltip-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}
</style>`;

function patchVictron(format) {
  const start = format.indexOf('  <div v-if="weekChart.length"');
  const end = format.indexOf('  <div v-if="!msg.payload?.timestamp"');
  if (start < 0 || end < 0) throw new Error("Victron chart block not found");

  let out = format.slice(0, start) + VICTRON_CHART_BLOCK + format.slice(end);

  out = out.replace(
    "data() { return { now: Date.now(), timer: null }; },",
    "data() { return { now: Date.now(), timer: null, chartHover: null }; },"
  );

  if (!out.includes("onChartMove(evt)")) {
    out = out.replace(
      "methods: {\n    sendCmd(action)",
      `methods: {${CHART_HELPERS}
    buildChartHover(point, px) {
      const specs = this.chartLegend;
      const rows = specs.map(s => ({
        key: s.key,
        label: s.label,
        color: s.color,
        value: this.formatChartVal(s.key, point[s.key])
      })).filter(r => r.value !== '—');
      let activeKey = rows.length ? rows.reduce((a, b) => {
        const av = Math.abs(Number(point[a.key]) || 0);
        const bv = Math.abs(Number(point[b.key]) || 0);
        return bv > av ? b : a;
      }).key : null;
      const dotLine = activeKey ? this.chartLines.find(l => l.key === activeKey) : null;
      let dot = null;
      if (activeKey && dotLine) {
        const v = Number(point[activeKey]);
        if (!Number.isNaN(v)) {
          const x = this.chartX(point.t);
          const y = activeKey === 'soc'
            ? 218 - (v / 100) * 206
            : 115 - (v / this.chartPowerMax) * 100;
          dot = { x, y, color: dotLine.color };
        }
      }
      return {
        px: Math.min(Math.max(px, 80), Math.max(80, px)),
        x: this.chartX(point.t),
        timeLabel: new Date(point.t).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }),
        rows,
        activeKey,
        dot
      };
    },
    formatChartVal(key, val) {
      if (val == null || val === '') return '—';
      const n = Number(val);
      if (Number.isNaN(n)) return String(val);
      if (key === 'soc') return Math.round(n) + '%';
      return Math.round(n) + ' W';
    },
    sendCmd(action)`
    );
  }

  if (!out.includes(".energy-chart-tooltip")) {
    out = out.replace("\n<script>", `${CHART_CSS}\n<script>`);
  }
  return out;
}

function patchHuawei(format) {
  const start = format.indexOf('  <div v-if="weekChart.length"');
  const end = format.indexOf('  <div v-if="!msg.payload?.timestamp"');
  if (start < 0 || end < 0) throw new Error("Huawei chart block not found");

  let out = format.slice(0, start) + HUAWEI_CHART_BLOCK + format.slice(end);

  out = out.replace(
    "data() { return { now: Date.now(), timer: null }; },",
    "data() { return { now: Date.now(), timer: null, chartHover: null }; },"
  );

  if (!out.includes("onChartMove(evt)")) {
    out = out.replace(
      "methods: {\n    pad2(n)",
      `methods: {${CHART_HELPERS}
    buildChartHover(point, px) {
      const v = Number(point.active);
      const pmax = this.chartPowerMax;
      const y = Number.isNaN(v) ? null : 100 - (v / pmax) * 88;
      return {
        px: Math.min(Math.max(px, 80), Math.max(80, px)),
        x: this.chartX(point.t),
        timeLabel: new Date(point.t).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }),
        value: this.formatChartVal(point.active),
        dot: y == null ? null : { x: this.chartX(point.t), y }
      };
    },
    formatChartVal(val) {
      if (val == null || val === '') return '—';
      const n = Number(val);
      return Number.isNaN(n) ? String(val) : Math.round(n) + ' W';
    },
    pad2(n)`
    );
  }

  if (!out.includes(".energy-chart-tooltip")) {
    out = out.replace("\n<script>", `${CHART_CSS}\n<script>`);
  }
  return out;
}

for (const [file, id, patchFn] of [
  ["811-victron-energy-status.json", "template_victron_energy_dashboard", patchVictron],
  ["821-huawei-energy-status.json", "template_huawei_energy_dashboard", patchHuawei],
]) {
  const path = join(flowsDir, file);
  const data = JSON.parse(readFileSync(path, "utf8"));
  const node = data.find((n) => n.id === id);
  node.format = patchFn(node.format);
  writeFileSync(path, `${JSON.stringify(data, null, 4)}\n`);
  console.log(`Patched ${file}`);
}
