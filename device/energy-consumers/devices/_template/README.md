# Consumer device template

Copy this folder to `devices/<your-consumer-id>/` and customize.

## Steps

1. Rename the parent folder to your consumer `id` (must match registry).
2. Copy `config.example.yaml` → `config.yaml` (gitignored on server).
3. Implement or wire `publisher.py` to publish:

   ```text
   energy/consumers/<id>/status   (retained JSON)
   ```

4. Add the consumer to `config/consumers_registry.yaml` with `enabled: true`.

## Example status payload

```json
{
  "consumer_id": "my-new-plug",
  "name": "My new smart plug",
  "power_w": 142.5,
  "energy_kwh": 12.34,
  "online": true,
  "source": "tuya_plug",
  "timestamp": "2026-07-05T12:00:00+00:00",
  "tags": ["basement"]
}
```

See `../../lib/consumer_schema.py` for the canonical schema.

## Test

```bash
mosquitto_pub -h 192.168.2.4 -t energy/consumers/my-new-plug/status -r \
  -m '{"consumer_id":"my-new-plug","name":"Test","power_w":0,"online":true,"source":"manual","timestamp":"2026-07-05T12:00:00+00:00"}'

mosquitto_sub -h 192.168.2.4 -t 'energy/consumers/#' -v
```
