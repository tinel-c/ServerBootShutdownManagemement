/**
 * Minimal client for Node-RED Admin HTTP API (same origin as the editor).
 * @see https://nodered.org/docs/api/admin/
 */

export function createClient(options) {
  const base = options.baseUrl.replace(/\/$/, "");
  /** Use JSON-only Accept so GET /nodes returns node list, not bundled HTML. */
  const headers = { Accept: "application/json" };

  if (options.bearerToken) {
    headers.Authorization = `Bearer ${options.bearerToken}`;
  } else if (options.username != null && options.password != null) {
    const b = Buffer.from(`${options.username}:${options.password}`).toString("base64");
    headers.Authorization = `Basic ${b}`;
  }

  async function request(path, { method = "GET", json, headers: extraHeaders } = {}) {
    const url = `${base}${path.startsWith("/") ? path : `/${path}`}`;
    const init = { method, headers: { ...headers, ...extraHeaders } };
    if (json !== undefined) {
      init.headers["Content-Type"] = "application/json";
      init.body = JSON.stringify(json);
    }
    const res = await fetch(url, init);
    const text = await res.text();
    if (!res.ok) {
      const err = new Error(`${res.status} ${res.statusText}: ${text.slice(0, 500)}`);
      err.status = res.status;
      throw err;
    }
    const ct = res.headers.get("content-type") || "";
    if (ct.includes("application/json")) {
      try {
        return JSON.parse(text);
      } catch {
        return text;
      }
    }
    return text;
  }

  return { baseUrl: base, request };
}

export function loadConfig() {
  const baseUrl = process.env.NODE_RED_BASE_URL || "http://192.168.2.4:1880";
  const bearerToken = process.env.NODE_RED_BEARER_TOKEN || "";
  const username = process.env.NODE_RED_USERNAME;
  const password = process.env.NODE_RED_PASSWORD;
  return {
    baseUrl,
    bearerToken: bearerToken || undefined,
    username: username || undefined,
    password: password !== undefined ? password : undefined,
  };
}
