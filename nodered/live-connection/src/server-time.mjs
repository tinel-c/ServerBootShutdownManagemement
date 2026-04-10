/**
 * Backup/snapshot folder names use the live Node-RED host clock and timezone
 * from GET /diagnostics (not the machine running npm).
 */

function formatFolderStamp(date, timeZone) {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).formatToParts(date);
  const p = Object.fromEntries(parts.filter((x) => x.type !== "literal").map((x) => [x.type, x.value]));
  return `${p.year}-${p.month}-${p.day}-${p.hour}-${p.minute}-${p.second}`;
}

/**
 * @returns {Promise<{
 *   stamp: string,
 *   diagnostics: object | null,
 *   timeZone: string,
 *   serverTimeUtc: string | null,
 *   serverTimeLocal: string | null,
 *   instantIso: string
 * }>}
 */
export async function resolveBackupStamp(client) {
  try {
    const diagnostics = await client.request("/diagnostics");
    const tz = diagnostics?.intl?.timeZone || "UTC";
    const utcStr = diagnostics?.time?.utc;
    const instant = utcStr ? new Date(utcStr) : new Date();
    const safeInstant = Number.isNaN(instant.getTime()) ? new Date() : instant;
    const stamp = formatFolderStamp(safeInstant, tz);
    return {
      stamp,
      diagnostics,
      timeZone: tz,
      serverTimeUtc: diagnostics?.time?.utc ?? null,
      serverTimeLocal: diagnostics?.time?.local ?? null,
      instantIso: safeInstant.toISOString(),
    };
  } catch {
    const instant = new Date();
    return {
      stamp: formatFolderStamp(instant, "UTC"),
      diagnostics: null,
      timeZone: "UTC",
      serverTimeUtc: null,
      serverTimeLocal: null,
      instantIso: instant.toISOString(),
    };
  }
}
