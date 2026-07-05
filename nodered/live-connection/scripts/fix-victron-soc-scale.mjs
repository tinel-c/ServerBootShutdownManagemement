import { readFileSync, writeFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const path = join(
  dirname(fileURLToPath(import.meta.url)),
  "..",
  "..",
  "flows",
  "811-victron-energy-status.json"
);
const data = JSON.parse(readFileSync(path, "utf8"));
const node = data.find((n) => n.id === "template_victron_energy_dashboard");
let f = node.format;

const oldSvg = `        <text x="12" y="120" fill="#64748b" font-size="10" font-weight="600">0 W</text>
        <text x="12" y="214" fill="#94a3b8" font-size="10" font-weight="600">SoC 100%</text>
        <text x="12" y="226" fill="#64748b" font-size="10" font-weight="600">0%</text>
        <line x1="10" y1="115" x2="790" y2="115" stroke="rgba(255,255,255,0.18)" stroke-width="0.8" stroke-dasharray="3 3"/>
        <line x1="10" y1="28" x2="790" y2="28" stroke="rgba(255,255,255,0.06)" stroke-width="0.6"/>
        <line x1="10" y1="218" x2="790" y2="218" stroke="rgba(255,255,255,0.06)" stroke-width="0.6"/>`;

const newSvg = `        <text x="12" y="120" fill="#64748b" font-size="10" font-weight="600">0 W</text>
        <text x="12" y="132" fill="#94a3b8" font-size="10" font-weight="600">SoC 100%</text>
        <text x="12" y="214" fill="#64748b" font-size="10" font-weight="600">0%</text>
        <line x1="10" y1="115" x2="790" y2="115" stroke="rgba(255,255,255,0.18)" stroke-width="0.8" stroke-dasharray="3 3"/>
        <line x1="10" y1="28" x2="790" y2="28" stroke="rgba(255,255,255,0.06)" stroke-width="0.6"/>
        <line x1="10" y1="138" x2="790" y2="138" stroke="rgba(45,212,191,0.12)" stroke-width="0.6"/>
        <line x1="10" y1="218" x2="790" y2="218" stroke="rgba(255,255,255,0.06)" stroke-width="0.6"/>`;

if (!f.includes(oldSvg)) throw new Error("Victron SVG labels block not found");
f = f.replace(oldSvg, newSvg);

const oldHoverInsert = `    buildChartHover(point, px, wrapW) {`;
const newHoverInsert = `    chartSocY(v) {
      const n = Number(v);
      const top = 138;
      const bottom = 218;
      if (Number.isNaN(n)) return bottom;
      return bottom - (Math.max(0, Math.min(100, n)) / 100) * (bottom - top);
    },
    buildChartHover(point, px, wrapW) {`;

if (!f.includes(oldHoverInsert)) throw new Error("buildChartHover not found");
f = f.replace(oldHoverInsert, newHoverInsert);

f = f.replace(
  `          const y = activeKey === 'soc'
            ? 218 - (v / 100) * 206
            : 115 - (v / this.chartPowerMax) * 100;`,
  `          const y = activeKey === 'soc'
            ? this.chartSocY(v)
            : 115 - (v / this.chartPowerMax) * 100;`
);

f = f.replace(
  `          const y = s.kind === 'soc' ? 218 - (v / 100) * 206 : 115 - (v / pmax) * 100;`,
  `          const y = s.kind === 'soc' ? this.chartSocY(v) : 115 - (v / pmax) * 100;`
);

node.format = f;
writeFileSync(path, `${JSON.stringify(data, null, 4)}\n`);
console.log("Patched Victron SoC scale (100% at top of SoC band)");
