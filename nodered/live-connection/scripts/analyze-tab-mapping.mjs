import { readFileSync, readdirSync, writeFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { createClient, loadConfig } from "../src/client.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(__dirname, "..", "..");
const flowsDir = join(repoRoot, "flows");

const files = readdirSync(flowsDir).filter((f) => f.endsWith(".json")).sort();

const config = loadConfig();
const client = createClient(config);
const live = await client.request("/flows");
const tabById = new Map();
for (const n of live) {
  if (n.type === "tab") tabById.set(n.id, (n.label || "").trim());
}

function analyzeFile(path) {
  const data = JSON.parse(readFileSync(path, "utf8"));
  if (!Array.isArray(data)) return { z: new Map(), nodeCount: 0 };
  const z = new Map();
  let nodeCount = 0;
  for (const n of data) {
    if (!n || typeof n !== "object") continue;
    nodeCount++;
    if (typeof n.z === "string" && n.z) {
      z.set(n.z, (z.get(n.z) || 0) + 1);
    }
  }
  return { z, nodeCount };
}

const perFile = [];
for (const f of files) {
  const { z, nodeCount } = analyzeFile(join(flowsDir, f));
  const zEntries = [...z.entries()].sort((a, b) => b[1] - a[1]);
  perFile.push({
    file: f,
    nodeCount,
    tabRefs: zEntries.map(([id, c]) => ({
      tabId: id,
      nodes: c,
      liveLabel: tabById.get(id) ?? null,
    })),
  });
}

const allTabIds = new Set();
for (const p of perFile) for (const t of p.tabRefs) allTabIds.add(t.tabId);

const liveTabIds = new Set([...tabById.keys()]);
const repoTabIdsNotOnLive = [...allTabIds].filter((id) => !liveTabIds.has(id));
const liveTabIdsNotInRepoFiles = [...liveTabIds].filter((id) => !allTabIds.has(id));

const out = {
  generatedAt: new Date().toISOString(),
  nodeRedBaseUrl: config.baseUrl,
  summary: {
    repoFlowFiles: files.length,
    uniqueTabIdsReferencedInRepo: allTabIds.size,
    liveFlowTabs: tabById.size,
  },
  repoTabIdsNotOnLive,
  liveTabIdsNotInRepoFiles,
  liveTabsOrdered: [...tabById.entries()]
    .map(([id, label]) => ({ tabId: id, label }))
    .sort((a, b) => a.label.localeCompare(b.label)),
  perFile,
};

const outPath = join(__dirname, "tab-mapping-analysis.json");
writeFileSync(outPath, JSON.stringify(out, null, 2), "utf8");
console.log("Wrote", outPath);
