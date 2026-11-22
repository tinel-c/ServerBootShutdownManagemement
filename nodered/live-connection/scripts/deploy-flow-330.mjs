/**
 * Deploy flow 330 (4-channel thyristor illumination) to live Node-RED.
 *   node nodered/live-connection/scripts/deploy-flow-330.mjs
 */
import { readFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { createClient, loadConfig } from "../src/client.mjs";

const here = dirname(fileURLToPath(import.meta.url));

const repoRoot = join(here, "..", "..");
const flowFile = "330-4ch-thyristor-illumination.json";
const patch = JSON.parse(readFileSync(join(repoRoot, "flows", flowFile), "utf8"));
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

function resolveThemeId(flows, wanted) {
  const themes = flows.filter((n) => n.type === "ui-theme");
  if (themes.some((t) => t.id === wanted)) return wanted;
  const page = flows.find(
    (n) => n.type === "ui-page" && n.theme && themes.some((t) => t.id === n.theme)
  );
  if (page) return page.theme;
  return themes[0]?.id || wanted;
}

if (!live.some((n) => n.id === "mqtt_broker_local")) {
  throw new Error("mqtt_broker_local is missing on Node-RED. Import 00-base-config.json first.");
}

const uiBaseId = resolveUiBaseId(live);
if (!uiBaseId) {
  throw new Error("No ui-base node on Node-RED. Import 00-base-config.json first.");
}

const themeId = resolveThemeId(live, "39a2cf2c0af73875");
const pathTaken = live.find(
  (n) => n.type === "ui-page" && n.path === "/illumination" && n.id !== "ui_page_4ch_thyristor"
);
if (pathTaken) {
  throw new Error(`Dashboard path /illumination is already used by ${pathTaken.id} (${pathTaken.name}).`);
}

const normalizedPatch = patch.map((n) => {
  if (n.type === "ui-page") return { ...n, ui: uiBaseId, theme: themeId };
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
      flow: flowFile,
      uiBaseId,
      themeId,
      liveNodesBefore: before,
      patchNodes: normalizedPatch.length,
      replacedExisting: removed,
      liveNodesAfter: merged.length,
      dashboard: "http://192.168.2.4:1880/dashboard/illumination",
    },
    null,
    2
  )
);
