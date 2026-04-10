import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { resolveBackupStamp } from "./server-time.mjs";

async function tryRequest(client, path) {
  try {
    const data = await client.request(path);
    return { ok: true, data };
  } catch (e) {
    return { ok: false, error: e.message, status: e.status };
  }
}

function uniqueNpmModules(nodesJson) {
  if (!Array.isArray(nodesJson)) return [];
  const names = new Set();
  for (const n of nodesJson) {
    if (n && typeof n.module === "string" && n.module) names.add(n.module);
  }
  return [...names].sort();
}

/**
 * Full HTTP export of what the Admin API exposes (flows, settings, palette, runtime hints).
 * Encrypted credential secrets live in flows_cred.json on the server filesystem — not in this export.
 */
export async function runBackup(client, rootDir) {
  const clock = await resolveBackupStamp(client);
  const dir = join(rootDir, "backups", `backup-${clock.stamp}`);
  mkdirSync(dir, { recursive: true });

  const flows = await client.request("/flows");
  writeFileSync(join(dir, "flows.json"), JSON.stringify(flows, null, 2), "utf8");

  const settings = await tryRequest(client, "/settings");
  if (settings.ok) {
    writeFileSync(join(dir, "settings.json"), JSON.stringify(settings.data, null, 2), "utf8");
  }

  const nodes = await tryRequest(client, "/nodes");
  if (nodes.ok) {
    writeFileSync(join(dir, "nodes.json"), JSON.stringify(nodes.data, null, 2), "utf8");
    const modules = uniqueNpmModules(nodes.data);
    const modulesExcludingCore = modules.filter((m) => m !== "node-red");
    writeFileSync(
      join(dir, "npm-modules.json"),
      JSON.stringify({ modules, modulesExcludingCore }, null, 2),
      "utf8"
    );
  }

  const flowsState = await tryRequest(client, "/flows/state");
  if (flowsState.ok) {
    writeFileSync(join(dir, "flows-state.json"), JSON.stringify(flowsState.data, null, 2), "utf8");
  }

  let diagnosticsWritten = false;
  if (clock.diagnostics) {
    writeFileSync(join(dir, "diagnostics.json"), JSON.stringify(clock.diagnostics, null, 2), "utf8");
    diagnosticsWritten = true;
  } else {
    const diagnostics = await tryRequest(client, "/diagnostics");
    if (diagnostics.ok) {
      writeFileSync(join(dir, "diagnostics.json"), JSON.stringify(diagnostics.data, null, 2), "utf8");
      diagnosticsWritten = true;
    }
  }

  const contextGlobal = await tryRequest(client, "/context/global");
  if (contextGlobal.ok) {
    const raw = JSON.stringify(contextGlobal.data, null, 2);
    writeFileSync(join(dir, "context-global.json"), raw, "utf8");
  }

  const manifest = {
    exportedAt: clock.instantIso,
    serverClock: {
      timeZone: clock.timeZone,
      utc: clock.serverTimeUtc,
      local: clock.serverTimeLocal,
      folderStamp: clock.stamp,
    },
    nodeRedBaseUrl: client.baseUrl,
    files: {
      "flows.json": { description: "Full flow configuration; import via Editor or POST /flows", required: true },
      "settings.json": { description: "Runtime settings from GET /settings (subset of full settings.js)" },
      "nodes.json": { description: "Installed palette nodes from GET /nodes" },
      "npm-modules.json": { description: "Unique npm module names for reinstalling dependencies" },
      "flows-state.json": { description: "Flow engine state" },
      "diagnostics.json": { description: "Runtime diagnostics snapshot" },
      "context-global.json": { description: "Global context store (memory/file); may contain sensitive data" },
    },
    partial: {
      settingsJson: settings.ok,
      nodesJson: nodes.ok,
      flowsStateJson: flowsState.ok,
      diagnosticsJson: diagnosticsWritten,
      contextGlobalJson: contextGlobal.ok,
    },
    limitations: [
      "Encrypted credentials are stored in flows_cred.json on the Node-RED userDir — not exposed by the HTTP API. After restore, re-enter passwords in credential nodes or restore flows_cred.json from a filesystem backup.",
      "Full settings.js (userDir) is not fully represented by GET /settings; copy settings.js manually if you rely on custom editorTheme, context storage paths, etc.",
    ],
  };

  writeFileSync(join(dir, "manifest.json"), JSON.stringify(manifest, null, 2), "utf8");

  return { dir, manifest };
}
