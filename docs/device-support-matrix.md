# AirGuard AI — Device Support Matrix

## Supported Integrations

### Home Assistant (Priority 1)
| Feature | Support Level | Notes |
|---------|--------------|-------|
| Authentication | ✅ Full | Long-lived access tokens |
| Entity discovery | ✅ Full | All sensor + controllable entities |
| Sensor readings | ✅ Full | Via REST API state polling + WebSocket subscription |
| Device control | ✅ Full | Via service calls (fan speed, on/off, etc.) |
| Real-time updates | ✅ Full | WebSocket state_changed subscription |
| History | ✅ Full | Via REST API /api/history/period/ |

**Supported entity types:**
- `sensor.*` — temperature, humidity, PM2.5, CO2, VOC, pressure
- `fan.*` — air purifiers with speed control
- `switch.*` — on/off devices
- `binary_sensor.*` — smoke/CO alarms, motion, occupancy

### MQTT (Priority 2)
| Feature | Support Level | Notes |
|---------|--------------|-------|
| Broker connection | ✅ Full | Username/password + TLS |
| Topic subscription | ✅ Full | Wildcard support |
| Payload parsing | ✅ Full | JSON payloads with configurable field mapping |
| Device commands | ✅ Full | Publish to command topics |
| Retained messages | ✅ Full | Handled on connect |
| LWT (availability) | ✅ Full | Online/offline detection |
| Home Assistant MQTT Discovery | ✅ Full | Auto-discover HA-configured MQTT devices |

### AirGradient (Priority 3)
| Feature | Support Level | Notes |
|---------|--------------|-------|
| Device discovery | ⚠️ Manual | mDNS or user-configured IP |
| Sensor readings | ✅ Full | GET /measures/current |
| PM1/PM2.5/PM10 | ✅ Full | Direct particle measurements |
| CO2 (NDIR) | ✅ Full | Labeled as direct CO2 |
| VOC/NOx index | ✅ Full | Sensirion SGP41 indices (labeled as index, not ppm) |
| Temperature | ✅ Full | Compensated values available |
| Humidity | ✅ Full | Compensated values available |
| Device control | ❌ None | Read-only monitor |
| Authentication | N/A | No auth required (local network) |
| Firmware req. | v3.0.10+ | For local HTTP API |

### ESPHome (Priority 4)
| Feature | Support Level | Notes |
|---------|--------------|-------|
| Connection | ⚠️ REST/SSE | Via web_server component |
| Sensor readings | ✅ Full | JSON state endpoint + SSE events |
| BME688 support | ⚠️ Partial | Raw measurements only (temp, humidity, pressure, gas resistance) |
| BSEC IAQ | ❌ Optional | Requires user-installed BSEC; cannot bundle |
| Device control | ⚠️ Limited | Switch/fan entities via REST |

### Generic REST/Webhook (Priority 5)
| Feature | Support Level | Notes |
|---------|--------------|-------|
| Arbitrary endpoints | ✅ Full | User-configured URL + auth |
| Field mapping | ✅ Full | JSONPath or dot-notation mapping |
| Authentication | ✅ Full | Bearer, API key, Basic |
| Rate limiting | ✅ Full | Configurable per-endpoint |

### Simulation (Priority 6)
| Feature | Support Level | Notes |
|---------|--------------|-------|
| Synthetic data | ✅ Full | All measurement types |
| Labeled as simulated | ✅ Required | SIMULATED provenance, visual badge |
| Event generation | ✅ Full | Configurable anomaly scenarios |

## Sensor Measurement Matrix

| Measurement | AirGradient | BME688 Raw | BME688+BSEC | HA Sensor | MQTT |
|-------------|-------------|-----------|-------------|-----------|------|
| PM1 | ✅ | ❌ | ❌ | ✅* | ✅* |
| PM2.5 | ✅ | ❌ | ❌ | ✅* | ✅* |
| PM10 | ✅ | ❌ | ❌ | ✅* | ✅* |
| CO2 (NDIR) | ✅ | ❌ | ❌ | ✅* | ✅* |
| eCO2 (estimated) | ❌ | ❌ | ✅ | ✅* | ✅* |
| VOC Index | ✅ | ❌ | ✅ | ✅* | ✅* |
| Gas Resistance | ❌ | ✅ | ✅ | ✅* | ✅* |
| Temperature | ✅ | ✅ | ✅ | ✅* | ✅* |
| Humidity | ✅ | ✅ | ✅ | ✅* | ✅* |
| Pressure | ❌ | ✅ | ✅ | ✅* | ✅* |
| NOx Index | ✅ | ❌ | ❌ | ✅* | ✅* |
| IAQ (Bosch) | ❌ | ❌ | ✅ | ✅* | ✅* |

*✅* = depends on connected device providing this measurement type

