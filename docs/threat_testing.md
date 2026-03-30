# AEGIS Threat Scenario Testing

Run repeatable threat scenarios:

```bash
cd gateway
python -m tests.threat_scenarios
```

Scenarios covered:
- replay attack
- delayed batch injection
- sequence discontinuity
- MQTT session interruption / liveness issue (forced requires_reset)
- benign normal traffic
- edge case duplicate packets

Each scenario reports:
- expected result
- actual result
- affected enforcement layer
- detection success/failure
- latency impact (ms)
