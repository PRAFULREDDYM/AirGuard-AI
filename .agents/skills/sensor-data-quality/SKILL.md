---
name: sensor-data-quality
description: >-
  Guide for sensor data schemas, unit conversion, timestamp handling, calibration tracking,
  drift detection, stale readings, missing data handling, and measurement provenance.
---

# Sensor Data Quality Skill

## Canonical Sensor Reading Schema

```python
class SensorReading(BaseModel):
    id: UUID
    device_id: str
    sensor_id: str
    timestamp: datetime          # UTC, from device
    measurement_type: MeasurementType  # Enum: PM25, PM10, VOC_INDEX, CO2, TEMP, HUMIDITY, etc.
    value: float
    unit: str                    # Controlled vocabulary: "µg/m³", "ppb", "°C", "%RH", etc.
    provenance: DataProvenance   # MEASURED, ESTIMATED, DERIVED, SIMULATED
    raw_value: float | None      # Original sensor value before calibration
    calibration_quality: CalibrationQuality  # UNCALIBRATED, WARMING_UP, CALIBRATED, DEGRADED
    source_integration: str      # "home_assistant", "mqtt", "airgradient", etc.
    ingestion_timestamp: datetime # When the backend received it
```

## Measurement Types (Controlled Vocabulary)

| Type           | Unit(s)         | Notes                                    |
|---------------|----------------|------------------------------------------|
| PM1            | µg/m³          | Direct particle measurement              |
| PM25           | µg/m³          | Direct particle measurement              |
| PM10           | µg/m³          | Direct particle measurement              |
| VOC_INDEX      | 1-500 (index)  | Relative, NOT absolute ppm               |
| VOC_RAW        | Ω (ohms)       | Raw gas resistance                       |
| CO2            | ppm            | NDIR direct measurement ONLY             |
| ECO2           | ppm            | Estimated from VOC, MUST be labeled      |
| TEMPERATURE    | °C             | Normalize from °F if needed              |
| HUMIDITY       | %RH            | Relative humidity                        |
| PRESSURE       | hPa            | Barometric pressure                      |
| NOX_INDEX      | 1-500 (index)  | Relative NOx index                       |
| GAS_RESISTANCE | Ω              | Raw MOX sensor resistance                |
| AQI            | 0-500          | Derived Air Quality Index                |

## Execution Procedure

### Ingesting a reading

1. Parse raw payload from adapter
2. Validate measurement type against controlled vocabulary
3. Normalize units (e.g., °F → °C, mg/m³ → µg/m³)
4. Check timestamp validity (not in future, not older than 24h)
5. Detect duplicates (same device + sensor + timestamp + type)
6. Check staleness (no reading in configured freshness window)
7. Record calibration status
8. Mark provenance (measured vs estimated vs simulated)
9. Persist to database
10. Forward to real-time subscribers

### Critical rules

- **eCO2 must be labeled ECO2**, never CO2
- **Missing ≠ 0:** Null/absent readings must not default to zero
- **Stale window:** Default 5 minutes; configurable per sensor type
- **Warm-up:** BME688 needs ~5 minutes; SGP4x needs ~60 seconds initial
- **Clock drift:** Accept ±60s offset, flag readings with >60s drift

## Validation Checklist

- [ ] All readings have UTC timestamps
- [ ] Unit normalization is applied consistently
- [ ] Duplicates are rejected
- [ ] Stale sensors are flagged in UI
- [ ] Raw vs derived values are preserved
- [ ] Missing data shows as unavailable, not zero
- [ ] eCO2 is never labeled as CO2
- [ ] Calibration quality is tracked per device
- [ ] Simulated data is marked with SIMULATED provenance

