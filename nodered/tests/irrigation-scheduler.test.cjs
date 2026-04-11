/**
 * Loads "Daily irrigation scheduler" from 421-irrigation-status-dashboard.json
 * and runs it with mocked flow + fixed time (TZ=UTC).
 *
 * Run: node nodered/tests/irrigation-scheduler.test.cjs
 */
'use strict';

process.env.TZ = 'UTC';

const fs = require('fs');
const path = require('path');
const assert = require('assert');

const FLOW_FILE = path.join(__dirname, '..', 'flows', '421-irrigation-status-dashboard.json');

function loadSchedulerFunc() {
  const nodes = JSON.parse(fs.readFileSync(FLOW_FILE, 'utf8'));
  const n = nodes.find((x) => x.id === 'fbc049d7179a9e0b');
  assert.ok(n && typeof n.func === 'string', 'Daily irrigation scheduler node (fbc049d7179a9e0b) not found');
  return n.func;
}

function createFlow(initial) {
  const store = Object.assign({}, initial);
  return {
    get(k) {
      return Object.prototype.hasOwnProperty.call(store, k) ? store[k] : undefined;
    },
    set(k, v) {
      store[k] = v;
    },
    snapshot() {
      return { ...store };
    },
  };
}

function withFixedTime(utcMs, fn) {
  const RealDate = Date;
  function FakeDate(...args) {
    if (args.length === 0) return new RealDate(utcMs);
    return new RealDate(...args);
  }
  FakeDate.prototype = RealDate.prototype;
  Object.setPrototypeOf(FakeDate, RealDate);
  FakeDate.now = () => utcMs;
  FakeDate.parse = RealDate.parse;
  FakeDate.UTC = RealDate.UTC;
  global.Date = FakeDate;
  try {
    return fn();
  } finally {
    global.Date = RealDate;
  }
}

function runScheduler(funcBody, flow, node) {
  const fn = new Function('flow', 'node', funcBody);
  return fn(flow, node || { status() {} });
}

function main() {
  const funcBody = loadSchedulerFunc();
  const nodeLog = { last: null, status(o) { this.last = o; } };
  let flow;
  let out;

  // --- Regression: seconds > 2 must NOT block (60s tick rarely lands in 0–2s) ---
  flow = createFlow({
    irrigation_scheduler_enabled: true,
    irrigation_sched_area_a_hour: 3,
    irrigation_sched_area_a_minute: 0,
    irrigation_sched_area_b_hour: 5,
    irrigation_sched_area_b_minute: 0,
    irrigation_weekdays_enabled: [true, false, true, false, true, false, true],
  });
  // Mon 13 Apr 2026 03:00:45 UTC — Monday slot enabled; dry (no weather)
  out = withFixedTime(Date.UTC(2026, 3, 13, 3, 0, 45), () => runScheduler(funcBody, flow, nodeLog));
  assert.deepStrictEqual(out[0], { payload: 'ON', topic: 'topic' });
  assert.strictEqual(out[1], null);
  assert.strictEqual(nodeLog.last && nodeLog.last.text, 'Start Lawn');

  // Same wall minute: already fired for this day → no duplicate
  out = withFixedTime(Date.UTC(2026, 3, 13, 3, 0, 12), () => runScheduler(funcBody, flow, nodeLog));
  assert.strictEqual(out[0], null);
  assert.strictEqual(out[1], null);

  // Flowers at 05:00:30 same Monday
  flow = createFlow({
    irrigation_scheduler_enabled: true,
    irrigation_sched_area_a_hour: 3,
    irrigation_sched_area_a_minute: 0,
    irrigation_sched_area_b_hour: 5,
    irrigation_sched_area_b_minute: 0,
    irrigation_weekdays_enabled: [true, false, true, false, true, false, true],
  });
  // Ensure lawn key from earlier test does not exist in this fresh store; flowers uses different key
  out = withFixedTime(Date.UTC(2026, 3, 13, 5, 0, 30), () => runScheduler(funcBody, flow, nodeLog));
  assert.strictEqual(out[0], null);
  assert.deepStrictEqual(out[1], { payload: 'ON', topic: 'topic' });
  assert.strictEqual(nodeLog.last.text, 'Start Flowers');

  // Scheduler disabled
  flow = createFlow({ irrigation_scheduler_enabled: false });
  out = withFixedTime(Date.UTC(2026, 3, 13, 3, 0, 10), () => runScheduler(funcBody, flow, nodeLog));
  assert.deepStrictEqual(out, [null, null]);

  // Winter (December) — lawn slot skipped, no ON
  flow = createFlow({
    irrigation_scheduler_enabled: true,
    irrigation_sched_area_a_hour: 3,
    irrigation_sched_area_a_minute: 0,
    irrigation_weekdays_enabled: [true, true, true, true, true, true, true],
  });
  out = withFixedTime(Date.UTC(2026, 11, 15, 3, 0, 20), () => runScheduler(funcBody, flow, nodeLog));
  assert.deepStrictEqual(out, [null, null]);
  assert.strictEqual(nodeLog.last.text, 'Skip Lawn (winter)');

  // Saturday — default weekdays have Saturday off
  flow = createFlow({
    irrigation_scheduler_enabled: true,
    irrigation_sched_area_a_hour: 3,
    irrigation_sched_area_a_minute: 0,
    irrigation_weekdays_enabled: [true, false, true, false, true, false, true],
  });
  // Sat 11 Apr 2026 03:00:15 UTC
  out = withFixedTime(Date.UTC(2026, 3, 11, 3, 0, 15), () => runScheduler(funcBody, flow, nodeLog));
  assert.deepStrictEqual(out, [null, null]);
  assert.strictEqual(nodeLog.last.text, 'Skip Lawn (day off)');

  // Wet day: lawn skipped after weekday check sets key; no ON
  flow = createFlow({
    irrigation_scheduler_enabled: true,
    irrigation_sched_area_a_hour: 3,
    irrigation_sched_area_a_minute: 0,
    irrigation_weekdays_enabled: [true, true, true, true, true, true, true],
    irrigation_weather_v1: {
      daily: [{ date: '2026-04-13', wet: true }],
    },
  });
  out = withFixedTime(Date.UTC(2026, 3, 13, 3, 0, 50), () => runScheduler(funcBody, flow, nodeLog));
  assert.deepStrictEqual(out, [null, null]);
  assert.strictEqual(nodeLog.last.text, 'Skip Lawn (rain)');

  console.log('All irrigation scheduler tests passed (7 cases).');
}

main();
