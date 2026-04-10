// Node-RED Function node: add module https in Setup → External modules (flow JSON "libs"). Sandbox has no require().

if (flow.get('irrigation_lat') == null) flow.set('irrigation_lat', 47.0966);

if (flow.get('irrigation_lon') == null) flow.set('irrigation_lon', 27.5632);

if (flow.get('irrigation_location_name') == null) flow.set('irrigation_location_name', 'Lunca Cetățuii, Iași, RO');

if (flow.get('irrigation_rain_skip_mm') == null) flow.set('irrigation_rain_skip_mm', 1);

if (flow.get('irrigation_rain_skip_prob') == null) flow.set('irrigation_rain_skip_prob', 70);



const lat = Number(flow.get('irrigation_lat'));

const lon = Number(flow.get('irrigation_lon'));

const rainMm = Number(flow.get('irrigation_rain_skip_mm'));

const probSkip = Number(flow.get('irrigation_rain_skip_prob'));

const locName = String(flow.get('irrigation_location_name') || 'Lunca Cetățuii, Iași, RO');



const url = 'https://api.open-meteo.com/v1/forecast?latitude=' + encodeURIComponent(lat) + '&longitude=' + encodeURIComponent(lon) +

    '&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max' +

    '&forecast_days=8&timezone=auto';



https.get(url, function (res) {

    let body = '';

    res.on('data', function (c) { body += c; });

    res.on('end', function () {

        const code = res.statusCode || 0;

        if (code < 200 || code >= 300) {

            node.error('Open-Meteo HTTP ' + code + ': ' + String(body).slice(0, 240));

            node.status({ fill: 'red', shape: 'ring', text: 'HTTP ' + code });

            return;

        }

        try {

            const j = JSON.parse(body);

            if (!j.daily || !j.daily.time || !j.daily.time.length) {

                node.error('Open-Meteo: missing daily data in response');

                node.status({ fill: 'red', shape: 'ring', text: 'Bad API shape' });

                return;

            }

            const t = j.daily.time;

            const daily = [];

            for (let i = 0; i < t.length; i++) {

                const pm = Number(j.daily.precipitation_sum[i] != null ? j.daily.precipitation_sum[i] : 0);

                const pp = Number(j.daily.precipitation_probability_max[i] != null ? j.daily.precipitation_probability_max[i] : 0);

                const wet = pm >= rainMm || pp >= probSkip;

                daily.push({

                    date: t[i],

                    precipMm: Math.round(pm * 10) / 10,

                    precipProb: Math.round(pp),

                    wmo: j.daily.weather_code[i],

                    tmax: Math.round(j.daily.temperature_2m_max[i]),

                    tmin: Math.round(j.daily.temperature_2m_min[i]),

                    wet: wet

                });

            }

            flow.set('irrigation_weather_v1', {

                fetchedAt: new Date().toISOString(),

                sourceName: 'Open-Meteo · ' + locName,

                sourceUrl: 'https://open-meteo.com',

                attribution: 'Weather data by Open-Meteo.com (CC BY 4.0)',

                apiHost: 'api.open-meteo.com',

                lat: lat,

                lon: lon,

                daily: daily

            });

            node.send({ topic: '__weather_refresh__', payload: '' });

            node.status({ fill: 'green', shape: 'dot', text: 'Weather OK' });

        } catch (e) {

            node.error('Open-Meteo: ' + e.message);

            node.status({ fill: 'red', shape: 'ring', text: 'Parse error' });

        }

    });

}).on('error', function (e) {

    node.error(e.message);

    node.status({ fill: 'red', shape: 'ring', text: 'HTTP error' });

});

return null;

