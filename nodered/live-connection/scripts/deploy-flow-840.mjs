import { readFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { spawnSync } from "child_process";
import { createClient, loadConfig } from "../src/client.mjs";

const repoRoot = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const flowFiles = ["840-energy-consumers.json"];

const patch = flowFiles.flatMap((name) => {
  const file = join(repoRoot, "flows", name);
  return JSON.parse(readFileSync(file, "utf8"));
});
const patchIds = new Set(patch.map((n) => n.id));

const client = createClient(loadConfig());
const live = await client.request("/flows");

const merged = live.filter((n) => !patchIds.has(n.id));
merged.push(...patch);

await client.request("/flows", {
  method: "POST",
  json: merged,
  headers: { "Node-RED-Deployment-Type": "full" },
});

const gen = spawnSync(process.execPath, ["scripts/generate-flow-840.mjs"], {
  cwd: join(repoRoot, "live-connection"),
  encoding: "utf8",
});

console.log(
  JSON.stringify(
    {
      ok: true,
      flowFiles,
      nodes: patch.length,
      consumers: patch.filter((n) => n.id?.startsWith("ui_group_consumer_")).length,
      generate: gen.stdout?.trim() || gen.stderr?.trim(),
      dashboardUrl: "/dashboard/energy",
    },
    null,
    2
  )
);
