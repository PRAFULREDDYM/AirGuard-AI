# AirGuard AI — Data Contracts

## Canonical Sensor Reading (API → DB → Frontend)

```json
{
  "id": "uuid-v4",
  "device_id": "string",
  "sensor_id": "string",
  "timestamp": "2024-01-15T10:30:00Z",
  "measurement_type": "PM25",
  "value": 12.5,
  "unit": "µg/m³",
  "provenance": "MEASURED",
  "raw_value": 12.8,
  "calibration_quality": "CALIBRATED",
  "source_integration": "airgradient",
  "ingestion_timestamp": "2024-01-15T10:30:01Z"
}
```

## Measurement Types (Enum)

```
PM1, PM25, PM10, VOC_INDEX, VOC_RAW, CO2, ECO2,
TEMPERATURE, HUMIDITY, PRESSURE, NOX_INDEX,
GAS_RESISTANCE, AQI, IAQ
```

## Data Provenance (Enum)

```
MEASURED    — Direct sensor measurement
ESTIMATED   — Derived from other measurements (e.g., eCO2)
DERIVED     — Calculated from multiple sensors (e.g., AQI)
SIMULATED   — Synthetic data for testing
IMPORTED    — From CSV or external dataset
```

## Calibration Quality (Enum)

```
UNCALIBRATED  — No calibration applied
WARMING_UP    — Sensor in warm-up period
CALIBRATED    — Factory or user calibration active
DEGRADED      — Calibration drift detected
UNKNOWN       — Calibration status unavailable
```

## Environmental Event

```json
{
  "id": "uuid-v4",
  "room_id": "uuid-v4",
  "event_type": "ANOMALY",
  "severity": "ELEVATED",
  "started_at": "2024-01-15T10:30:00Z",
  "ended_at": "2024-01-15T10:45:00Z",
  "trigger_readings": ["reading-id-1", "reading-id-2"],
  "anomaly_score": 0.87,
  "classification": null,
  "classification_confidence": null,
  "model_version_id": null,
  "acknowledged": false,
  "notes": null
}
```

## Automation Rule

```json
{
  "id": "uuid-v4",
  "name": "Auto purify on high PM2.5",
  "enabled": true,
  "trigger": {
    "measurement_type": "PM25",
    "condition": "ABOVE",
    "threshold": 35.0,
    "duration_seconds": 300,
    "hysteresis": 5.0
  },
  "action": {
    "device_id": "purifier-uuid",
    "command": "set_speed",
    "parameters": {"speed": "high"}
  },
  "constraints": {
    "room_id": "room-uuid",
    "cooldown_seconds": 1800,
    "max_executions_per_hour": 4,
    "requires_data_validity": true
  }
}
```

## Device Capability Manifest

```json
{
  "device_id": "string",
  "manufacturer": "AirGradient",
  "model": "ONE",
  "firmware_version": "3.1.4",
  "connection_protocol": "airgradient_local",
  "measurements": [
    {"type": "PM25", "unit": "µg/m³", "provenance": "MEASURED"},
    {"type": "CO2", "unit": "ppm", "provenance": "MEASURED"},
    {"type": "VOC_INDEX", "unit": "index", "provenance": "ESTIMATED"}
  ],
  "controls": [],
  "polling_interval_seconds": 10,
  "supports_streaming": false,
  "calibration_status": "CALIBRATED",
  "room_id": "uuid-v4"
}
```

## WebSocket Events (API → Frontend)

```json
{"type": "reading", "data": { /* SensorReading */ }}
{"type": "event", "data": { /* EnvironmentalEvent */ }}
{"type": "device_status", "data": {"device_id": "...", "status": "online"}}
{"type": "automation_executed", "data": { /* AutomationExecution */ }}
```

