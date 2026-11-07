# AirGuard AI — Mode 1: Monitor & Notify Specification

## Overview

**Monitor & Notify** is AirGuard AI's default operating mode. It provides consumer-friendly, high-fidelity environmental monitoring, historical analytics, and multi-channel alerting without permitting any automated physical actuator control.

---

## Functional Scope

1. **Telemetry Ingestion & Quality Monitoring**:
   - Ingests PM1.0, PM2.5, PM10, CO2 (NDIR), VOC Index, Temperature, and Relative Humidity.
   - Enforces strict sensor data provenance: distinguishes direct electrochemical/optical measurements from derived estimates.
   - Evaluates data freshness window (stale flag triggered when readings exceed 120 seconds).
   - Sensor warmup gating: suppresses anomaly scoring during initial sensor stabilization.

2. **In-App Notification Center**:
   - Centralized feed located in global header and settings.
   - Distinct categories:
     - `AIR_QUALITY`: Threshold excursions (e.g. PM2.5 elevated, poor ventilation).
     - `SAFETY_ALERT`: Life-safety guidance (elevated combustible gas, smoke detected).
     - `SYSTEM`: Sensor offline, stale telemetry, battery status.
     - `MAINTENANCE`: Filter life countdown, sensor recalibration notice.
   - Delivery states: `DISPATCHED`, `DELIVERED`, `READ`.
   - Read/unread status tracking with batch "Mark All as Read" support.

3. **Notification Preferences & Quiet Hours**:
   - **Quiet Hours**: Configurable suppression window (default `22:00` to `07:00`). Non-critical alerts are buffered until quiet hours expire.
   - **Emergency Exemption**: Critical safety alerts (e.g., life-safety smoke/gas advice) ignore quiet hours.
   - **Alert Cooldown**: 15-minute deduplication window per room/event to prevent notification spam during sustained environmental spikes.

4. **Zero-Actuation Invariant**:
   - Under Monitor & Notify mode, `DEVICE_CONTROL` permission remains ungranted.
   - The backend `SafetyEngine` rejects any command dispatch with `403 Forbidden` (`CONSENT REQUIRED: DEVICE_CONTROL`).

---

## API Endpoints

- `GET /api/v1/notifications/preferences`: Retrieves user quiet hours and alert category preferences.
- `POST /api/v1/notifications/preferences`: Updates alert category toggles, min severity, and cooldowns.
- `GET /api/v1/notifications/history`: Fetches paginated in-app notifications with read status.
- `PATCH /api/v1/notifications/{id}/read`: Marks a single notification as read.
- `POST /api/v1/notifications/mark-all-read`: Marks all pending notifications as read.
- `POST /api/v1/notifications/test`: Dispatches a simulated test alert to verify notification delivery.

