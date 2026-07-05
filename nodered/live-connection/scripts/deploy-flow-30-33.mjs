import { readFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { createClient, loadConfig } from "../src/client.mjs";

const repoRoot = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const flowFiles = [
  "09-media-base-config.json",
  "30-media-server-controls.json",
  "31-media-server-status.json",
  "32-media-server-health.json",
  "33-media-server-schedule.json",
];

const patch = flowFiles.flatMap((name) => {
  const file = join(repoRoot, "flows", name);
  return JSON.parse(readFileSync(file, "utf8"));
});
const patchIds = new Set(patch.map((n) => n.id));

const client = createClient(loadConfig());
const live = await client.request("/flows");

const before = live.length;
const merged = live.filter((n) => !patchIds.has(n.id));
const removed = before - merged.length;
merged.push(...patch);

await client.request("/flows", {
  method: "POST",
  json: merged,
  headers: { "Node-RED-Deployment-Type": "full" },
});

console.log(
  JSON.stringify(
    {
      ok: true,
      flowFiles,
      liveNodesBefore: before,
      patchNodes: patch.length,
      replacedExisting: removed,
      liveNodesAfter: merged.length,
    },
    null,
    2
  )
);
