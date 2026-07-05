import { readFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { createClient, loadConfig } from "../src/client.mjs";

const repoRoot = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const flowFiles = [
  "800-energy-base-config.json",
  "811-victron-energy-status.json",
  "821-huawei-energy-status.json",
];

const patch = flowFiles.flatMap((file) =>
  JSON.parse(readFileSync(join(repoRoot, "flows", file), "utf8"))
);
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

const after = await client.request("/flows");
const huaweiGroup = after.find((n) => n.id === "ui_group_huawei_energy");

console.log(
  JSON.stringify(
    {
      ok: true,
      flows: flowFiles,
      liveNodesBefore: before,
      patchNodes: patch.length,
      replacedExisting: removed,
      liveNodesAfter: merged.length,
      ui_group_huawei_energy: huaweiGroup
        ? { name: huaweiGroup.name, page: huaweiGroup.page, order: huaweiGroup.order }
        : "MISSING",
    },
    null,
    2
  )
);
