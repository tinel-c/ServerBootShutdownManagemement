import { readFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { createClient, loadConfig } from "../src/client.mjs";

const repoRoot = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const patchFile = join(repoRoot, "flows", "613-watchdog-status-dashboard.json");
const patch = JSON.parse(readFileSync(patchFile, "utf8"));
const patchIds = new Set(patch.map((n) => n.id));

const client = createClient(loadConfig());
const live = await client.request("/flows");

function resolveUiBaseId(flows) {
  const bases = flows.filter((n) => n.type === "ui-base");
  const preferred = bases.find((n) => n.id === "ui_base" || n.name === "Server Management");
  if (preferred) return preferred.id;
  if (bases.length === 1) return bases[0].id;
  return null;
}

const uiBaseId = resolveUiBaseId(live);
if (!uiBaseId) {
  throw new Error("No ui-base node on Node-RED. Import 00-base-config.json first.");
}

const normalizedPatch = patch.map((n) => {
  if (n.type === "ui-page" && n.ui) return { ...n, ui: uiBaseId };
  return n;
});

const before = live.length;
const merged = live.filter((n) => !patchIds.has(n.id));
const removed = before - merged.length;
merged.push(...normalizedPatch);

await client.request("/flows", {
  method: "POST",
  json: merged,
  headers: { "Node-RED-Deployment-Type": "full" },
});

console.log(
  JSON.stringify(
    {
      ok: true,
      uiBaseId,
      liveNodesBefore: before,
      patchNodes: normalizedPatch.length,
      replacedExisting: removed,
      liveNodesAfter: merged.length,
    },
    null,
    2
  )
);
