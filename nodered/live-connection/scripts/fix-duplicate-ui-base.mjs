/**
 * FlowFuse Dashboard allows only one ui-base node.
 * Keeps ui_base (Server Management) and repoints pages from duplicate bases.
 */
import { createClient, loadConfig } from "../src/client.mjs";

const KEEP_BASE_ID = "ui_base";

const client = createClient(loadConfig());
const live = await client.request("/flows");

const uiBases = live.filter((n) => n.type === "ui-base");
const removeIds = new Set(
  uiBases.filter((n) => n.id !== KEEP_BASE_ID).map((n) => n.id)
);

if (removeIds.size === 0) {
  console.log(JSON.stringify({ ok: true, message: "Already single ui-base", kept: KEEP_BASE_ID }));
  process.exit(0);
}

const merged = live
  .filter((n) => !removeIds.has(n.id))
  .map((n) => {
    if (n.type === "ui-page" && n.ui && removeIds.has(n.ui)) {
      return { ...n, ui: KEEP_BASE_ID };
    }
    return n;
  });

await client.request("/flows", {
  method: "POST",
  json: merged,
  headers: { "Node-RED-Deployment-Type": "full" },
});

console.log(
  JSON.stringify(
    {
      ok: true,
      kept: KEEP_BASE_ID,
      removedUiBases: [...removeIds],
      liveNodesBefore: live.length,
      liveNodesAfter: merged.length,
    },
    null,
    2
  )
);
