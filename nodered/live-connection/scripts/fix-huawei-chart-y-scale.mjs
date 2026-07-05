import { readFileSync, writeFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const path = join(
  dirname(fileURLToPath(import.meta.url)),
  "..",
  "..",
  "flows",
  "821-huawei-energy-status.json"
);
const data = JSON.parse(readFileSync(path, "utf8"));
const node = data.find((n) => n.id === "template_huawei_energy_dashboard");
let f = node.format;

const oldSvg = `        <text x="12" y="16" fill="#94a3b8" font-size="10" font-weight="600">{{ chartPowerMax }} W</text>
        <text x="12" y="104" fill="#64748b" font-size="10" font-weight="600">0 W</text>
        <line x1="10" y1="100" x2="790" y2="100" stroke="rgba(255,255,255,0.18)" stroke-width="0.8" stroke-dasharray="3 3"/>
        <line x1="10" y1="24" x2="790" y2="24" stroke="rgba(255,255,255,0.06)" stroke-width="0.6"/>
        <line x1="10" y1="176" x2="790" y2="176" stroke="rgba(255,255,255,0.06)" stroke-width="0.6"/>
        <g v-for="(tick,i) in chartXTicks" :key="'x'+i">
          <line :x1="tick.x" y1="12" :x2="tick.x" y2="180" stroke="rgba(255,255,255,0.06)" stroke-width="0.6"/>
          <text :x="tick.x" y="196" fill="#94a3b8" font-size="10" font-weight="600" text-anchor="middle">{{ tick.label }}</text>
        </g>
        <line v-if="chartHover" :x1="chartHover.x" y1="12" :x2="chartHover.x" y2="180" stroke="rgba(255,255,255,0.35)" stroke-width="0.8"/>`;

const newSvg = `        <text x="12" y="18" fill="#94a3b8" font-size="10" font-weight="600">{{ chartPowerMax }} W</text>
        <text x="12" y="170" fill="#64748b" font-size="10" font-weight="600">0 W</text>
        <line x1="10" y1="24" x2="790" y2="24" stroke="rgba(255,255,255,0.06)" stroke-width="0.6"/>
        <line x1="10" y1="168" x2="790" y2="168" stroke="rgba(255,255,255,0.18)" stroke-width="0.8" stroke-dasharray="3 3"/>
        <g v-for="(tick,i) in chartXTicks" :key="'x'+i">
          <line :x1="tick.x" y1="24" :x2="tick.x" y2="168" stroke="rgba(255,255,255,0.06)" stroke-width="0.6"/>
          <text :x="tick.x" y="196" fill="#94a3b8" font-size="10" font-weight="600" text-anchor="middle">{{ tick.label }}</text>
        </g>
        <line v-if="chartHover" :x1="chartHover.x" y1="24" :x2="chartHover.x" y2="168" stroke="rgba(255,255,255,0.35)" stroke-width="0.8"/>`;

if (!f.includes(oldSvg)) {
  throw new Error("Huawei chart SVG block not found");
}
f = f.replace(oldSvg, newSvg);

const oldBuild = `    buildChartHover(point, px, wrapW) {
      const v = Number(point.active);
      const pmax = this.chartPowerMax;
      const y = Number.isNaN(v) ? null : 100 - (v / pmax) * 88;`;

const newBuild = `    chartPowerY(v) {
      const pmax = this.chartPowerMax;
      const n = Number(v);
      const top = 24;
      const bottom = 168;
      if (Number.isNaN(n) || pmax <= 0) return bottom;
      return bottom - (Math.max(0, n) / pmax) * (bottom - top);
    },
    buildChartHover(point, px, wrapW) {
      const v = Number(point.active);
      const y = Number.isNaN(v) ? null : this.chartPowerY(v);`;

if (!f.includes(oldBuild)) {
  throw new Error("buildChartHover block not found");
}
f = f.replace(oldBuild, newBuild);

const oldPath = `        const y = 100 - (v / pmax) * 88;`;
const newPath = `        const y = this.chartPowerY(v);`;

if (!f.includes(oldPath)) {
  throw new Error("powerPath y formula not found");
}
f = f.replace(oldPath, newPath);

node.format = f;
writeFileSync(path, `${JSON.stringify(data, null, 4)}\n`);
console.log("Patched Huawei chart Y scale (0 at bottom)");
