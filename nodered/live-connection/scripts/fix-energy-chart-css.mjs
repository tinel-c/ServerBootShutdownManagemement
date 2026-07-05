import { readFileSync, writeFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

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

const flowsDir = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "flows");

for (const [file, id] of [
  ["811-victron-energy-status.json", "template_victron_energy_dashboard"],
  ["821-huawei-energy-status.json", "template_huawei_energy_dashboard"],
]) {
  const path = join(flowsDir, file);
  const data = JSON.parse(readFileSync(path, "utf8"));
  const node = data.find((n) => n.id === id);
  let f = node.format;

  f = f.replace(/\n<style>\n\.energy-chart-wrap[\s\S]*?<\/style>\n(?=<\/script>)/, "");

  if (!f.includes(".energy-chart-wrap .energy-chart-tooltip")) {
    f = f.replace("\n<script>", `${CHART_CSS}\n<script>`);
  }

  node.format = f;
  writeFileSync(path, `${JSON.stringify(data, null, 4)}\n`);
  const si = f.indexOf("<script>");
  const ei = f.indexOf("</script>");
  const inScript = f.slice(si, ei).includes(".energy-chart-tooltip");
  console.log(`${file}: css in script=${inScript}, has css=${f.includes(".energy-chart-tooltip")}`);
}
