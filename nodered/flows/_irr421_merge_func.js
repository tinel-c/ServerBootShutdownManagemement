const topic = msg.topic || '';
const raw = msg.payload;
function payloadToPowerString(r) {
    if (r === null || r === undefined || r === '') return 'UNKNOWN';
    if (Buffer.isBuffer(r)) return r.toString().trim();
    if (typeof r === 'object') {
        if (r.POWER !== undefined) return String(r.POWER).trim();
        if (r.POWER1 !== undefined) return String(r.POWER1).trim();
        for (const k of Object.keys(r)) {
            if (/^POWER\d+$/i.test(k) && r[k] !== undefined) return String(r[k]).trim();
        }
    }
    return String(r).trim();
}
function resolveTelegramChatIds() {
    const fromFlow = flow.get('telegram_chat_ids') || [];
    if (fromFlow.length) return fromFlow;
    try {
        const g = global.get('telegram_chat_ids');
        if (g && g.length) return g;
    } catch (e) {}
    return [991635368];
}
const pl = payloadToPowerString(raw);

const ZONE_KEYS = ['POWER2', 'POWER3', 'POWER4', 'POWER5', 'POWER10', 'POWER11', 'POWER12', 'POWER13', 'POWER14', 'POWER15', 'POWER16', 'POWER17'];

const POWER_TO_I = { POWER2: 'I1', POWER3: 'I2', POWER4: 'I3', POWER5: 'I4', POWER10: 'I5', POWER11: 'I6', POWER12: 'I7', POWER13: 'I8', POWER14: 'I9', POWER15: 'I10', POWER16: 'I11', POWER17: 'I12' };
const ZONE_KEYS_AREA_A = ['POWER2', 'POWER3', 'POWER4', 'POWER5', 'POWER10', 'POWER11', 'POWER12', 'POWER13', 'POWER14', 'POWER15'];
const ZONE_KEYS_AREA_B = ['POWER16', 'POWER17'];
const ZONE_KEY_TO_ICON = { POWER2: '🌱', POWER3: '🌿', POWER4: '🍃', POWER5: '🌾', POWER10: '🥬', POWER11: '🌽', POWER12: '🍅', POWER13: '🫛', POWER14: '🌻', POWER15: '🪴', POWER16: '🌳', POWER17: '🏞️' };
const LOG_MAX = 25;
let smsLine = null;
function pushLog(icon, line) {
    const arr = flow.get('irrigation_event_log_v1') || [];
    arr.unshift({ ts: new Date().toISOString(), icon: icon || '📋', line: String(line || '') });
    while (arr.length > LOG_MAX) arr.pop();
    flow.set('irrigation_event_log_v1', arr);
    smsLine = String(line || '');
}

function buildSmsOut() {
    let to = String(flow.get('irrigation_sms_to') || '').replace(/\D/g, '');
    if (!to || to.length < 8) {
        to = String(flow.get('sms_phone') || '').replace(/\D/g, '');
    }
    if (!to || to.length < 8 || !smsLine) return null;
    const text = ('Irrigation: ' + smsLine).substring(0, 160);
    return { topic: 'sms/gateway/command/send', payload: JSON.stringify({ to: to, text: text }) };
}

function buildTelegramTrigger() {
    if (!smsLine) return null;
    const ids = resolveTelegramChatIds();
    if (!ids.length) return null;
    return { payload: { irrigationTgAlert: smsLine } };
}

function pad2(n) { return (n < 10 ? '0' : '') + n; }
function localYmd(d) {
    return d.getFullYear() + '-' + pad2(d.getMonth() + 1) + '-' + pad2(d.getDate());
}
function wmoEmoji(code) {
    const c = Number(code) || 0;
    if (c === 0) return '☀️';
    if (c <= 3) return '🌤️';
    if (c <= 48) return '☁️';
    if (c <= 67) return '🌧️';
    if (c <= 77) return '🌨️';
    if (c <= 82) return '🌧️';
    return '⛈️';
}
function isDayWet(dateStr) {
    const w = flow.get('irrigation_weather_v1');
    if (!w || !w.daily || !w.daily.length) return false;
    const row = w.daily.find(function (x) { return x.date === dateStr; });
    return row ? !!row.wet : false;
}
/** Same rules as UI schedCountdown: time until next run epoch (rain-postponed slot from computeNextIrrigationSlot). */
function fmtCountdownTo(targetMs, nowMs) {
    if (targetMs == null || isNaN(targetMs)) return '—';
    let sec = Math.floor((targetMs - nowMs) / 1000);
    if (sec <= 0) return 'imminent';
    const d = Math.floor(sec / 86400);
    sec %= 86400;
    const h = Math.floor(sec / 3600);
    sec %= 3600;
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    if (d > 0) return d + 'd ' + h + 'h';
    if (h > 0) return h + 'h ' + m + 'm';
    if (m > 0) return m + 'm ' + s + 's';
    return s + 's';
}
function fmtNextRunPlannedLine(ms) {
    if (ms == null || isNaN(ms)) return '—';
    try {
        const d = new Date(ms);
        return d.toLocaleString(undefined, { weekday: 'long', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
    } catch (e) {
        return '—';
    }
}
/**
 * Next irrigation window: greedy forward scan over calendar days (horizon 14).
 * For each future local time (day + clock hour/min), skip if that calendar day is "wet"
 * (same rule as runtime: precip ≥ threshold OR prob ≥ threshold). First non-wet day wins.
 * This matches common rule-based irrigation practice (skip rain; wait for next suitable day).
 * Advanced systems add soil water balance / ET₀ − rain; we stay forecast-rule-based.
 */
function computeNextIrrigationSlot(hour, minute, nowMs) {
    const w = flow.get('irrigation_weather_v1');
    const daily = w && w.daily ? w.daily : [];
    const skippedDates = [];
    for (let add = 0; add < 14; add++) {
        const d = new Date(nowMs);
        d.setHours(0, 0, 0, 0);
        d.setDate(d.getDate() + add);
        const ds = localYmd(d);
        const slot = new Date(d);
        slot.setHours(Number(hour) || 0, Number(minute) || 0, 0, 0);
        if (slot.getTime() <= nowMs) continue;
        const row = daily.find(function (x) { return x.date === ds; });
        const wet = row ? !!row.wet : false;
        if (wet) {
            skippedDates.push(ds);
            continue;
        }
        let statusLine = '';
        if (skippedDates.length === 0) {
            statusLine = 'Next run targets the first upcoming dry day at your set time.';
        } else {
            statusLine = 'Forecast wet — postponed ' + skippedDates.length + ' day(s); next run on the next dry day at your set time.';
        }
        return { ms: slot.getTime(), skippedCount: skippedDates.length, skippedDates: skippedDates, statusLine: statusLine };
    }
    return { ms: null, skippedCount: skippedDates.length, skippedDates: skippedDates, statusLine: 'No dry day within 14-day forecast — check thresholds or weather fetch.' };
}
function computeNextRunMs(hour, minute, nowMs) {
    const r = computeNextIrrigationSlot(hour, minute, nowMs);
    return r.ms;
}
function buildWeatherUi(nowMs) {
    const w = flow.get('irrigation_weather_v1');
    if (!w || !w.daily || !w.daily.length) {
        return {
            hasData: false,
            days: [],
            attribution: 'Open-Meteo (CC BY 4.0)',
            sourceName: '—',
            fetchedAt: null,
            detailUrl: 'https://open-meteo.com'
        };
    }
    const days = w.daily.slice(0, 7).map(function (d) {
        const barPct = Math.min(100, Math.round((Number(d.precipMm) || 0) * 20));
        return {
            date: d.date,
            dayShort: (function () {
                try {
                    return new Date(d.date + 'T12:00:00').toLocaleDateString(undefined, { weekday: 'short' });
                } catch (e) {
                    return d.date;
                }
            })(),
            icon: wmoEmoji(d.wmo),
            tmax: d.tmax,
            tmin: d.tmin,
            precipMm: d.precipMm,
            precipProb: d.precipProb,
            wet: !!d.wet,
            barPct: barPct
        };
    });
    return {
        hasData: true,
        days: days,
        attribution: w.attribution || 'Weather data by Open-Meteo (CC BY 4.0)',
        sourceName: w.sourceName || 'Open-Meteo',
        fetchedAt: w.fetchedAt,
        detailUrl: w.sourceUrl || 'https://open-meteo.com',
        lat: w.lat,
        lon: w.lon
    };
}
function buildScheduleUi(nowMs) {
    const en = flow.get('irrigation_scheduler_enabled');
    const enabled = en !== false;
    const hA = Number(flow.get('irrigation_sched_area_a_hour'));
    const mA = Number(flow.get('irrigation_sched_area_a_minute'));
    const hB = Number(flow.get('irrigation_sched_area_b_hour'));
    const mB = Number(flow.get('irrigation_sched_area_b_minute'));
    const hourA = isNaN(hA) ? 3 : hA;
    const minA = isNaN(mA) ? 0 : mA;
    const hourB = isNaN(hB) ? 5 : hB;
    const minB = isNaN(mB) ? 0 : mB;
    const rainMm = Number(flow.get('irrigation_rain_skip_mm'));
    const rainProb = Number(flow.get('irrigation_rain_skip_prob'));
    const rMm = isNaN(rainMm) ? 1 : rainMm;
    const rPr = isNaN(rainProb) ? 70 : rainProb;
    const slotA = enabled ? computeNextIrrigationSlot(hourA, minA, nowMs) : { ms: null, skippedCount: 0, statusLine: '', skippedDates: [] };
    const slotB = enabled ? computeNextIrrigationSlot(hourB, minB, nowMs) : { ms: null, skippedCount: 0, statusLine: '', skippedDates: [] };
    const nextA = slotA.ms;
    const nextB = slotB.ms;
    const today = localYmd(new Date(nowMs));
    const wetToday = isDayWet(today);
    const logicIntro = 'A day is “wet” when forecast precipitation ≥ ' + rMm + ' mm or max rain probability ≥ ' + rPr + '%. The next irrigation is the first future day at your clock time that is not wet (dry / “sunny enough” for our rule).';
    const logicAlgorithm = 'Algorithm: greedy forward scan — walk from today up to 14 days; at each scheduled local time, skip wet days; the first dry day is the next run. This follows common rule-based irrigation (skip incoming rain; irrigate on the next suitable day). Advanced ET/soil-balance scheduling (e.g. FAO-56) can refine amounts; this flow uses forecast gates only.';
    return {
        enabled: enabled,
        areaAHour: hourA,
        areaAMin: minA,
        areaBHour: hourB,
        areaBMin: minB,
        rainSkipMm: rMm,
        rainSkipProb: rPr,
        wetToday: wetToday,
        wetTodayHint: wetToday ? 'Today’s forecast is wet — automatic start will skip until a dry day.' : 'Today’s forecast is dry at decision time (per daily flags).',
        nextA: nextA,
        nextB: nextB,
        countdownA: fmtCountdownTo(nextA, nowMs),
        countdownB: fmtCountdownTo(nextB, nowMs),
        labelA: nextA ? new Date(nextA).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' }) : '—',
        labelB: nextB ? new Date(nextB).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' }) : '—',
        lawnDetail: enabled ? slotA.statusLine : 'Scheduler disabled.',
        flowersDetail: enabled ? slotB.statusLine : 'Scheduler disabled.',
        lawnSkipped: slotA.skippedCount,
        flowersSkipped: slotB.skippedCount,
        logicTitle: 'Rain-smart schedule',
        nextLawnPlanned: enabled ? fmtNextRunPlannedLine(nextA) : 'Scheduler off',
        nextFlowersPlanned: enabled ? fmtNextRunPlannedLine(nextB) : 'Scheduler off',
        logicIntro: logicIntro,
        logicAlgorithm: logicAlgorithm,
        note: 'Lawn runs the full Lawn program; Flowers runs the Flowers program. Times are local to Node-RED.'
    };
}

const defaults = () => ({
    POWER1: 'UNKNOWN', POWER2: 'UNKNOWN', POWER3: 'UNKNOWN', POWER4: 'UNKNOWN', POWER5: 'UNKNOWN',
    POWER10: 'UNKNOWN', POWER11: 'UNKNOWN', POWER12: 'UNKNOWN', POWER13: 'UNKNOWN',
    POWER14: 'UNKNOWN', POWER15: 'UNKNOWN', POWER16: 'UNKNOWN', POWER17: 'UNKNOWN',
    pump: 'UNKNOWN',
    lastUpdate: null
});

function norm(v) {
    const u = String(v).toUpperCase();
    if (u === 'ON' || u === 'TRUE' || u === '1') return 'ON';
    if (u === 'OFF' || u === 'FALSE' || u === '0') return 'OFF';
    return u;
}

function fmtDur(totalSec) {
    const s = Math.max(0, Math.floor(Number(totalSec) || 0));
    if (s < 60) return s + 's';
    const m = Math.floor(s / 60);
    const r = s % 60;
    if (m < 60) return m + 'm ' + r + 's';
    const h = Math.floor(m / 60);
    return h + 'h ' + (m % 60) + 'm';
}

function fmtClock(ms) {
    if (!ms) return '—';
    try { return new Date(ms).toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'medium' }); } catch (e) { return '—'; }
}

function updateTimer(timers, key, prev, next) {
    if (!timers[key]) {
        timers[key] = { startedAt: null, lastEndIso: null, lastStartIso: null, lastDurationSec: null };
    }
    const t = timers[key];
    const p = (prev === 'ON' || prev === 'OFF') ? prev : null;
    const n = (next === 'ON' || next === 'OFF') ? next : null;
    if (n === 'ON' && p !== 'ON') {
        t.startedAt = Date.now();
        t.lastStartIso = new Date(t.startedAt).toISOString();
    }
    if (n === 'OFF' && p === 'ON' && t.startedAt) {
        const end = Date.now();
        t.lastEndIso = new Date(end).toISOString();
        t.lastDurationSec = Math.round((end - t.startedAt) / 1000);
        t.startedAt = null;
    }
}

function buildPayload(s, timers, now) {
    const nowMs = now || Date.now();
    const pumpUrl = flow.get('pump_web_url') || '';

    const zoneRows = [
        { k: 'POWER2', label: 'I1', icon: '🌱' },
        { k: 'POWER3', label: 'I2', icon: '🌿' },
        { k: 'POWER4', label: 'I3', icon: '🍃' },
        { k: 'POWER5', label: 'I4', icon: '🌾' },
        { k: 'POWER10', label: 'I5', icon: '🥬' },
        { k: 'POWER11', label: 'I6', icon: '🌽' },
        { k: 'POWER12', label: 'I7', icon: '🍅' },
        { k: 'POWER13', label: 'I8', icon: '🫛' },
        { k: 'POWER14', label: 'I9', icon: '🌻' },
        { k: 'POWER15', label: 'I10', icon: '🪴' },
        { k: 'POWER16', label: 'I11', icon: '🌳' },
        { k: 'POWER17', label: 'I12', icon: '🏞️' }
    ];
    const zonesAreaA = ZONE_KEYS_AREA_A.map(k => {
        const z = zoneRows.find(r => r.k === k);
        const ex = zoneExtras(k);
        return { ...z, state: s[k] || 'UNKNOWN', ...ex };
    });
    const zonesAreaB = ZONE_KEYS_AREA_B.map(k => {
        const z = zoneRows.find(r => r.k === k);
        const ex = zoneExtras(k);
        return { ...z, state: s[k] || 'UNKNOWN', ...ex };
    });

    function zoneExtras(key) {
        const st = s[key] || 'UNKNOWN';
        const tk = timers[key] || {};
        let zoneStarted = '';
        let zoneEnded = '';
        let zoneDuration = '';
        if (st === 'ON' && tk.startedAt) {
            const sec = Math.floor((nowMs - tk.startedAt) / 1000);
            zoneStarted = fmtClock(tk.startedAt);
            zoneEnded = '—';
            zoneDuration = fmtDur(sec);
        } else if (st === 'OFF') {
            if (tk.lastStartIso && tk.lastEndIso && tk.lastDurationSec != null) {
                zoneStarted = fmtClock(new Date(tk.lastStartIso).getTime());
                zoneEnded = fmtClock(new Date(tk.lastEndIso).getTime());
                zoneDuration = fmtDur(tk.lastDurationSec);
            } else if (tk.lastDurationSec != null) {
                zoneDuration = fmtDur(tk.lastDurationSec);
            }
        }
        return { zoneStarted, zoneEnded, zoneDuration };
    }

    const tp = timers.pump || {};
    const pumpSt = s.pump || 'UNKNOWN';
    let pumpRun = '';
    let pumpHist = '';
    if (pumpSt === 'ON' && tp.startedAt) {
        const sec = Math.floor((nowMs - tp.startedAt) / 1000);
        pumpRun = 'Running ' + fmtDur(sec) + ' · started ' + fmtClock(tp.startedAt);
    } else if (pumpSt === 'OFF' && tp.lastDurationSec != null && tp.lastStartIso && tp.lastEndIso) {
        pumpHist = 'Last: ' + fmtClock(new Date(tp.lastStartIso).getTime()) + ' → ' + fmtClock(new Date(tp.lastEndIso).getTime()) + ' · ' + fmtDur(tp.lastDurationSec);
    }

    const wx = buildWeatherUi(nowMs);
    const sch = buildScheduleUi(nowMs);
    if (wx.hasData && wx.days && wx.days.length) {
        const lawnY = sch.enabled && sch.nextA != null ? localYmd(new Date(sch.nextA)) : null;
        const flowersY = sch.enabled && sch.nextB != null ? localYmd(new Date(sch.nextB)) : null;
        wx.days = wx.days.map(function (day) {
            return {
                date: day.date,
                dayShort: day.dayShort,
                icon: day.icon,
                tmax: day.tmax,
                tmin: day.tmin,
                precipMm: day.precipMm,
                precipProb: day.precipProb,
                wet: day.wet,
                barPct: day.barPct,
                plannedLawn: lawnY != null && day.date === lawnY,
                plannedFlowers: flowersY != null && day.date === flowersY
            };
        });
    }

    return {
        power24: s.POWER1 || 'UNKNOWN',
        pump: pumpSt,
        pumpRunLine: pumpRun,
        pumpHistLine: pumpHist,
        pumpWebUrl: pumpUrl,
        zonesAreaA: zonesAreaA,
        zonesAreaB: zonesAreaB,
        eventLog: flow.get('irrigation_event_log_v1') || [],
        lastUpdate: s.lastUpdate,
        weatherUi: wx,
        scheduleUi: sch
    };
}

if (topic === '__weather_refresh__') {
    const s = flow.get('irrigation_status_v1') || defaults();
    const timers = flow.get('irrigation_zone_timers') || {};
    msg.payload = buildPayload(s, timers, Date.now());
    return [msg, null, null];
}

if (topic === '__init__') {
    const s = flow.get('irrigation_status_v1') || defaults();
    const timers = flow.get('irrigation_zone_timers') || {};
    msg.payload = buildPayload(s, timers, Date.now());
    return [msg, null, null];
}

if (topic === '__tick__') {
    const s = flow.get('irrigation_status_v1') || defaults();
    const timers = flow.get('irrigation_zone_timers') || {};
    msg.payload = buildPayload(s, timers, Date.now());
    return [msg, null, null];
}

if (topic.indexOf('tele/pompaApa/STATE') >= 0) {
    try {
        const o = typeof raw === 'object' ? raw : JSON.parse(String(raw));
        const ip = o.IPAddress || (o.Wifi && (o.Wifi.IP || o.Wifi.IPAddress || o.Wifi.ip)) || '';
        if (ip) flow.set('pump_web_url', 'http://' + ip + '/');
    } catch (e) { /* ignore */ }
    const s = flow.get('irrigation_status_v1') || defaults();
    const timers = flow.get('irrigation_zone_timers') || {};
    msg.payload = buildPayload(s, timers, Date.now());
    return [msg, null, null];
}

let s = flow.get('irrigation_status_v1') || defaults();
let timers = flow.get('irrigation_zone_timers') || {};

if (topic.indexOf('IrigationSystem') >= 0) {
    const seg = topic.split('/');
    const key = seg[seg.length - 1];
    if (key && key.indexOf('POWER') === 0) {
        const prev = norm(s[key]);
        const next = norm(pl);
        s[key] = next;
        if (ZONE_KEYS.indexOf(key) >= 0) {
            updateTimer(timers, key, prev, next);
        }
        if (prev !== next && (next === 'ON' || next === 'OFF')) {
            if (key === 'POWER1') {
                pushLog('⚡', next === 'ON' ? '24V power on' : '24V power off');
            } else if (ZONE_KEYS.indexOf(key) >= 0) {
                const lbl = POWER_TO_I[key] || key;
                const ic = ZONE_KEY_TO_ICON[key] || '🌿';
                pushLog(ic, next === 'ON' ? ('Start irrigation in ' + lbl) : ('Stop irrigation in ' + lbl));
            }
        }
    }
} else if (topic.indexOf('stat/pompaApa/POWER1') >= 0) {
    const prev = norm(s.pump);
    const next = norm(pl);
    s.pump = next;
    updateTimer(timers, 'pump', prev, next);
    if (prev !== next && (next === 'ON' || next === 'OFF')) {
        pushLog('💧', next === 'ON' ? 'Start pump' : 'Stop pump');
    }
}

s.lastUpdate = new Date().toISOString();
flow.set('irrigation_status_v1', s);
flow.set('irrigation_zone_timers', timers);
msg.payload = buildPayload(s, timers, Date.now());
return [msg, buildSmsOut(), buildTelegramTrigger()];
