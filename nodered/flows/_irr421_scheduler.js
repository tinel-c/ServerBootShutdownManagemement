if (flow.get('irrigation_sched_area_a_hour') == null) flow.set('irrigation_sched_area_a_hour', 3);
if (flow.get('irrigation_sched_area_a_minute') == null) flow.set('irrigation_sched_area_a_minute', 0);
if (flow.get('irrigation_sched_area_b_hour') == null) flow.set('irrigation_sched_area_b_hour', 5);
if (flow.get('irrigation_sched_area_b_minute') == null) flow.set('irrigation_sched_area_b_minute', 0);

const enabled = flow.get('irrigation_scheduler_enabled') !== false;
if (!enabled) {
    node.status({ fill: 'grey', shape: 'ring', text: 'Scheduler off' });
    return [null, null];
}

const now = new Date();
const ymd = now.getFullYear() + '-' + (now.getMonth() < 9 ? '0' : '') + (now.getMonth() + 1) + '-' + (now.getDate() < 10 ? '0' : '') + now.getDate();
const h = now.getHours();
const mi = now.getMinutes();
const s = now.getSeconds();

if (s > 2) return [null, null];

const hA = Number(flow.get('irrigation_sched_area_a_hour'));
const mA = Number(flow.get('irrigation_sched_area_a_minute'));
const hB = Number(flow.get('irrigation_sched_area_b_hour'));
const mB = Number(flow.get('irrigation_sched_area_b_minute'));
const hourA = isNaN(hA) ? 3 : hA;
const minA = isNaN(mA) ? 0 : mA;
const hourB = isNaN(hB) ? 5 : hB;
const minB = isNaN(mB) ? 0 : mB;

function isDayWet(dateStr) {
    const w = flow.get('irrigation_weather_v1');
    if (!w || !w.daily || !w.daily.length) return false;
    const row = w.daily.find(function (x) { return x.date === dateStr; });
    return row ? !!row.wet : false;
}

const startMsg = { payload: 'ON', topic: 'topic' };

if (h === hourA && mi === minA) {
    const key = 'sched_fired_lawn_' + ymd;
    if (flow.get(key)) return [null, null];
    flow.set(key, true);
    if (isDayWet(ymd)) {
        node.status({ fill: 'yellow', shape: 'dot', text: 'Skip Lawn (rain)' });
        return [null, null];
    }
    node.status({ fill: 'green', shape: 'dot', text: 'Start Lawn' });
    return [startMsg, null];
}

if (h === hourB && mi === minB) {
    const key = 'sched_fired_flowers_' + ymd;
    if (flow.get(key)) return [null, null];
    flow.set(key, true);
    if (isDayWet(ymd)) {
        node.status({ fill: 'yellow', shape: 'dot', text: 'Skip Flowers (rain)' });
        return [null, null];
    }
    node.status({ fill: 'green', shape: 'dot', text: 'Start Flowers' });
    return [null, startMsg];
}

return [null, null];
