import { readFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { createClient, loadConfig } from "../src/client.mjs";

const repoRoot = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const patchFile = join(repoRoot, "flows", "611-camera-management.json");
const patch = JSON.parse(readFileSync(patchFile, "utf8"));
const patchIds = new Set(patch.map((n) => n.id));
/** Legacy empty Camera page/group on live Node-RED (replaced by flow 611). */
const staleIds = new Set(["4021706cef5d7a9a", "bbb46a2633e48fe9"]);

const client = createClient(loadConfig());
const live = await client.request("/flows");

const before = live.length;
const merged = live.filter((n) => !patchIds.has(n.id) && !staleIds.has(n.id));
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
      liveNodesBefore: before,
      patchNodes: patch.length,
      replacedExisting: removed,
      liveNodesAfter: merged.length,
    },
    null,
    2
  )
);
