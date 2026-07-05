import { readFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { createClient, loadConfig } from "../src/client.mjs";

const repoRoot = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const flowFiles = ["50-telegram-interface.json"];

const patch = flowFiles.flatMap((name) => {
  const file = join(repoRoot, "flows", name);
  return JSON.parse(readFileSync(file, "utf8"));
});
const patchIds = new Set(patch.map((n) => n.id));

const client = createClient(loadConfig());
const live = await client.request("/flows");

/** Resolve the live telegram bot config node id (telegram bot or legacy telegrambot-config). */
function resolveTelegramBotId(flows) {
  const configs = flows.filter(
    (n) => n.type === "telegram bot" || n.type === "telegrambot-config"
  );
  const preferred = configs.find(
    (n) =>
      n.botname === "LuncaCetatuiiAutomationBot_bot" ||
      n.name === "LuncaCetatuiiAutomationBot_bot" ||
      n.id === "LuncaCetatuiiAutomationBot_bot"
  );
  if (preferred) return preferred.id;
  if (configs.length === 1) return configs[0].id;
  return null;
}

const botId = resolveTelegramBotId(live);
if (!botId) {
  throw new Error(
    "No telegram bot config on Node-RED. Configure the LuncaCetatuiiAutomationBot_bot node in the editor first."
  );
}

const TELEGRAM_NODE_TYPES = new Set([
  "telegram sender",
  "telegram receiver",
  "telegram event",
]);

// Drop legacy config from patch if live already has a bot config (avoid duplicate / type clash).
const patchWithoutConfig = patch.filter((n) => {
  if (n.type !== "telegrambot-config") return true;
  return !live.some((x) => x.type === "telegram bot" || x.type === "telegrambot-config");
});

const normalizedPatch = patchWithoutConfig.map((n) => {
  if (!TELEGRAM_NODE_TYPES.has(n.type) || !n.bot) return n;
  return { ...n, bot: botId };
});

const merged = live.filter((n) => !patchIds.has(n.id));
merged.push(...normalizedPatch);

// Rewire any orphaned telegram nodes still pointing at missing config ids.
const validBotIds = new Set(
  merged
    .filter((n) => n.type === "telegram bot" || n.type === "telegrambot-config")
    .map((n) => n.id)
);
for (const node of merged) {
  if (TELEGRAM_NODE_TYPES.has(node.type) && node.bot && !validBotIds.has(node.bot)) {
    node.bot = botId;
  }
}

await client.request("/flows", {
  method: "POST",
  json: merged,
  headers: { "Node-RED-Deployment-Type": "full" },
});

const rewired = merged.filter(
  (n) => TELEGRAM_NODE_TYPES.has(n.type) && n.bot === botId
).length;

console.log(
  JSON.stringify(
    {
      ok: true,
      flowFiles,
      telegramBotId: botId,
      nodesPatched: normalizedPatch.length,
      telegramNodesUsingBot: rewired,
    },
    null,
    2
  )
);
