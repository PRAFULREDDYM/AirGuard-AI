---
name: device-connectivity
description: >-
  Guide for implementing and debugging device connectivity adapters for Home Assistant,
  MQTT, ESPHome, AirGradient, REST APIs. Covers capability discovery, authentication,
  device lifecycle management, and connection troubleshooting.
---

# Device Connectivity Skill

## Purpose
Ensure all device adapters follow the capability-based adapter interface pattern and correctly handle authentication, discovery, telemetry, control, and lifecycle events.

## Adapter Interface Contract

Every adapter MUST implement these methods:

```python
class DeviceAdapter(Protocol):
    async def discover(self) -> list[DiscoveredDevice]
    async def authenticate(self, credentials: AdapterCredentials) -> AuthResult
    async def test_connection(self) -> ConnectionStatus
    async def list_devices(self) -> list[DeviceInfo]
    async def get_capabilities(self, device_id: str) -> DeviceCapabilities
    async def read_telemetry(self, device_id: str) -> list[SensorReading]
    async def subscribe(self, device_id: str, callback: TelemetryCallback) -> Subscription
    async def send_command(self, device_id: str, command: DeviceCommand) -> CommandResult
    async def health_check(self) -> AdapterHealth
    async def reconnect(self) -> ConnectionStatus
    async def disconnect(self) -> None
```

## Execution Procedure

### Adding a new adapter

1. Create adapter module in `services/integrations/adapters/{name}_adapter.py`
2. Implement the `DeviceAdapter` protocol
3. Define adapter-specific credential model (Pydantic)
4. Implement capability manifest generation from device metadata
5. Add connection test endpoint
6. Add mock/simulation variant for testing
7. Write integration tests with mock server
8. Document supported devices and limitations

### Authentication patterns

| Provider       | Auth Method                    | Token Storage      |
|---------------|-------------------------------|-------------------|
| Home Assistant | Long-lived access token        | Encrypted DB field |
| MQTT           | Username/password or TLS cert  | Encrypted DB field |
| AirGradient    | None (local network)           | N/A               |
| ESPHome        | API password or noise encryption| Encrypted DB field |
| REST/Webhook   | Bearer token, API key, or Basic| Encrypted DB field |

### Connection lifecycle

1. **Pairing:** User selects provider → enters credentials → test connection → discover devices
2. **Active:** Adapter polls or subscribes → validates data → forwards to ingestion
3. **Degraded:** Connection lost → exponential backoff reconnect → mark readings stale
4. **Disconnected:** User disconnects or adapter fails permanently → log and notify

## Validation Checklist

- [ ] Adapter implements all protocol methods
- [ ] Credentials are never logged or exposed in API responses
- [ ] Connection test validates before saving credentials
- [ ] Device capabilities are read from the device, not hardcoded
- [ ] Telemetry includes proper timestamps and provenance
- [ ] Control commands check device capability before sending
- [ ] Reconnection uses exponential backoff with jitter
- [ ] Mock variant exists for testing
- [ ] Integration test covers happy path and error cases
- [ ] Stale readings are detected and flagged

## References

- Home Assistant REST API: https://developers.home-assistant.io/docs/api/rest/
- Home Assistant WebSocket API: https://developers.home-assistant.io/docs/api/websocket/
- Paho MQTT: https://eclipse.dev/paho/files/paho.mqtt.python/html/
- AirGradient API: https://www.airgradient.com/documentation/local-server/
- ESPHome: https://esphome.io/

