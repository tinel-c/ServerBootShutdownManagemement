/**
 * Fix dashboard layout on live Node-RED:
 * - Rename duplicate "Home" (/page1) → Acvariu
 * - Hide legacy duplicate server groups on /home
 * - Remove orphaned media groups and last-command widget
 * - Move Rolling Log to end of Server page; full-width media widgets
 */
import { createClient, loadConfig } from "../src/client.mjs";

const SERVER_PAGE_ID = "5d4e0a738cb39e94";
const SERVER_GROUP_ID = "590309fda6555eae";
const AQUARIUM_PAGE_ID = "7fd05c7d064cc1bd";
const LEGACY_HOME_PAGE_ID = "ui_page_home";
const ROLLING_LOG_ID = "8a8dea15ce9f6c64";

const HIDE_GROUP_IDS = new Set([
  "ui_group_dell",
  "ui_group_hp",
  "ui_group_dell_health",
  "ui_group_hp_health",
  "ui_group_media",
  "ui_group_media_health",
]);

const REMOVE_GROUP_IDS = new Set([
  "ui_group_media",
  "ui_group_media_health",
  "ui_group_media_schedule",
]);

const REMOVE_NODE_IDS = new Set(["template_media_last_cmd"]);

const FULL_WIDTH = { width: 0, height: 0 };
const WIDGET_LAYOUT = {
  [ROLLING_LOG_ID]: { order: 30, ...FULL_WIDTH },
  ui_template_media_health: { order: 21, ...FULL_WIDTH },
  template_media_status: { order: 20, ...FULL_WIDTH },
  media_sched_ui_template: { group: SERVER_GROUP_ID, order: 22, ...FULL_WIDTH },
};

const client = createClient(loadConfig());
const flows = await client.request("/flows");

let changed = 0;

const patched = flows
  .filter((n) => !REMOVE_GROUP_IDS.has(n.id) && !REMOVE_NODE_IDS.has(n.id))
  .map((n) => {
    const copy = { ...n };

    if (copy.id === AQUARIUM_PAGE_ID && copy.type === "ui-page") {
      if (copy.name === "Home") {
        copy.name = "Acvariu";
        copy.icon = copy.icon || "lightbulb";
        copy.order = copy.order ?? 3;
        changed++;
      }
    }

    if (copy.id === LEGACY_HOME_PAGE_ID && copy.type === "ui-page") {
      copy.name = "Legacy";
      copy.order = 99;
      changed++;
    }

    if (copy.type === "ui-group" && copy.page === LEGACY_HOME_PAGE_ID && HIDE_GROUP_IDS.has(copy.id)) {
      copy.visible = "false";
      changed++;
    }

    const layout = WIDGET_LAYOUT[copy.id];
    if (layout) {
      for (const [key, value] of Object.entries(layout)) {
        if (copy[key] !== value) {
          copy[key] = value;
          changed++;
        }
      }
    }

    if (copy.id === ROLLING_LOG_ID && copy.type === "ui-template") {
      const tightLog =
        '<div id="log-console" style="margin:0;padding:0;"><div style="background-color:#1a1a1a;color:#00ff00;font-family:Consolas,monospace;padding:8px 10px;border-radius:8px;border:1px solid rgba(0,255,0,0.15);max-height:280px;overflow-y:auto;">\n' +
        '    <div v-for="line in msg.payload.slice(-12).reverse()" :key="line.timestamp + line.message" style="margin-bottom:2px;line-height:1.35;">\n' +
        '        <span style="color:#888;">[{{line.timestamp}}]</span> \n' +
        '        <span style="color:#ccc;font-weight:bold;">[{{line.source}}]</span> \n' +
        '        <span :class="line.class">{{line.message}}</span>\n' +
        "    </div>\n" +
        "</div></div>\n\n" +
        "<style>\n" +
        ".text-info { color: #2196f3; }\n" +
        ".text-success { color: #4caf50; }\n" +
        ".text-warning { color: #ff9800; }\n" +
        ".text-danger { color: #f44336; }\n" +
        "</style>";
      if (copy.format !== tightLog) {
        copy.format = tightLog;
        changed++;
      }
    }

    return copy;
  });

await client.request("/flows", {
  method: "POST",
  json: patched,
  headers: { "Node-RED-Deployment-Type": "full" },
});

console.log(
  JSON.stringify(
    {
      ok: true,
      layoutFixesApplied: changed,
      serverPage: SERVER_PAGE_ID,
      rollingLogOrder: 30,
      removedNodes: [...REMOVE_NODE_IDS],
      dashboardUrl: "/dashboard/page2",
    },
    null,
    2
  )
);
