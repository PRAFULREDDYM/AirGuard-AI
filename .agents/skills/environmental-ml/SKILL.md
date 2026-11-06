---
name: environmental-ml
description: >-
  Guide for environmental anomaly detection, electronic-nose feature extraction,
  sensor-pattern classification, unknown-class handling, uncertainty calibration,
  and model monitoring using real sensor data.
---

# Environmental ML Skill

## Purpose
Build ML models that analyze real sensor timeseries data to detect anomalies and classify environmental events.

## Model Hierarchy

### Level 1: Rule-Based Monitoring (always available)
- Threshold alerts on individual measurements
- Configurable per measurement type and room
- No training data needed
- Examples: PM2.5 > 35 µg/m³ for 10 minutes

### Level 2: Anomaly Detection (needs baseline data)
- Statistical deviation from per-room baseline
- Requires minimum baseline period (configurable, default 48 hours)
- Isolation Forest or similar unsupervised algorithm
- Reports anomaly score, not event class

### Level 3: Supervised Classification (needs labeled sessions)
- Trained on user-labeled sensor recording sessions
- Safe classes only: cooking, coffee, cleaning, baseline, unknown
- Requires grouped cross-validation (by session, not by timepoint)
- Must include unknown/OOD rejection

## Data Collection Module

```python
class DataCollectionSession(BaseModel):
    session_id: UUID
    device_id: str
    room_id: str
    start_time: datetime
    end_time: datetime | None
    label: str | None           # User-assigned after collection
    label_source: str           # "user_manual", "imported"
    sensor_model: str
    firmware_version: str | None
    environmental_conditions: dict  # temp, humidity at start
    notes: str | None
    readings: list[SensorReading]
```

## Feature Extraction

For sensor timeseries windows:
1. Statistical features: mean, std, min, max, slope, delta
2. Temporal features: time-of-day, duration above threshold
3. Cross-sensor features: temp/humidity correction ratios
4. Frequency features: if sampling rate permits

## Training Protocol

1. Collect labeled sessions (minimum 10 per class recommended)
2. Extract features per session window
3. Split by session ID (NOT by individual readings)
4. Train baseline classifier (Random Forest or Gradient Boosting)
5. Add unknown class rejection (threshold on max probability)
6. Evaluate: per-class precision/recall, confusion matrix, FAR, missed rate
7. Calibrate probabilities (Platt scaling or isotonic)
8. Register model with full metadata

## Validation Checklist

- [ ] Baseline collection period enforced before anomaly detection activates
- [ ] Session-grouped splits prevent temporal leakage
- [ ] Unknown/OOD class properly handled
- [ ] Humidity and temperature variations represented in training data
- [ ] Untrained models report "not trained" status
- [ ] Model never auto-promotes to production
- [ ] No hazardous materials used in data collection
- [ ] Per-class metrics reported (not just accuracy)
- [ ] Calibration quality assessed

