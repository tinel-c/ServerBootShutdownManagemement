import { readFileSync, writeFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const flowsDir = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "flows");

for (const [file, id] of [
  ["811-victron-energy-status.json", "template_victron_energy_dashboard"],
  ["821-huawei-energy-status.json", "template_huawei_energy_dashboard"],
]) {
  const path = join(flowsDir, file);
  const data = JSON.parse(readFileSync(path, "utf8"));
  const node = data.find((n) => n.id === id);
  let f = node.format;

  f = f.replace(
    ':opacity="chartHover ? (chartHover.activeKey === line.key ? 1 : 0.28) : 0.92"',
    'opacity="0.92"'
  );
  f = f.replace(
    "this.chartHover = this.buildChartHover(best, px);",
    "this.chartHover = this.buildChartHover(best, px, rect.width);"
  );
  f = f.replace("buildChartHover(point, px) {", "buildChartHover(point, px, wrapW) {");
  f = f.replace(
    "px: Math.min(Math.max(px, 80), Math.max(80, px)),",
    "px: Math.min(Math.max(px, 72), Math.max(72, (wrapW || 400) - 72)),"
  );

  node.format = f;
  writeFileSync(path, `${JSON.stringify(data, null, 4)}\n`);
  console.log(`Fixed ${file}`);
}
