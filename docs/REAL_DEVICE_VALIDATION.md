# AirGuard AI — Real Device Validation Guide

This document outlines the step-by-step procedures required to connect, calibrate, and verify physical hardware devices with AirGuard AI.

---

## 1. AirGradient ONE (Physical Monitor Validation)

### Prerequisites
- AirGradient ONE monitor (Indoor v9 or Outdoor v3) powered on.
- Firmware version **3.0.10+** (which exposes the local HTTP server).
- Device connected to the same local WiFi network as the AirGuard host.

### Step-by-Step Validation Procedure
1. **Find Device IP:**
   - Locate the device IP from your router DHCP table or mDNS (`http://airgradient_<serial>.local`).
2. **Verify Raw HTTP Response:**
   ```bash
   curl -s http://<DEVICE_IP>/measures/current | jq .
   ```
   *Expected response:* JSON containing `pm02`, `rco2`, `tvocIndex`, `noxIndex`, `atmpCompensated`, and `rhumCompensated`.
3. **Pair in AirGuard UI:**
   - Navigate to **Devices → Connect New Device**.
   - Select **AirGradient Local API**.
   - Enter device IP and click **Test Connection & Discover**.
   - Assign the discovered monitor to a designated Room.
4. **Data Verification Checklist:**
   - [ ] PM2.5 readings appear in Room overview with unit `µg/m³`.
   - [ ] CO2 is labeled as direct measurement (`CO2`), not estimated (`ECO2`).
   - [ ] VOC and NOx indices appear as relative indices (`index`), not absolute concentration.
   - [ ] Signal freshness updates every 10–30 seconds.

---

## 2. Home Assistant Integration Validation

### Prerequisites
- Home Assistant instance (Core or OS) running locally on LAN.
- At least one environmental sensor entity (e.g. `sensor.living_room_pm25`).
- At least one controllable fan or purifier entity (e.g. `fan.xiaomi_air_purifier`).

### Step-by-Step Validation Procedure
1. **Generate Token in Home Assistant:**
   - Profile → Long-Lived Access Tokens → Create Token.
2. **Pair in AirGuard UI:**
   - Go to **Devices → Connect New Device → Home Assistant**.
   - Input instance URL (`http://homeassistant.local:8123`) and paste Bearer token.
   - Click **Test Connection**.
3. **Entity Discovery & Permission:**
   - Verify all `sensor.*` and `fan.*` entities are listed.
   - Assign entities to corresponding rooms.
   - Toggle **Automation Permission** to ON for the fan entity if automated control is desired.
4. **Actuation Verification:**
   - In Room Details, test clicking **High Speed** or **Turn Off**.
   - Confirm Home Assistant state log registers the corresponding service call (`fan.set_percentage` or `fan.turn_off`).
   - Confirm command appears in AirGuard's **Automation Execution Audit Trail**.

---

## 3. MQTT Sensor Node (ESPHome / Bosch BME688)

### Prerequisites
- ESP32 running ESPHome with BME688 sensor (see `firmware/examples/esphome_bme688.yaml`).
- Mosquitto MQTT broker running on LAN (port 1883).

### Step-by-Step Validation Procedure
1. **Verify Broker Publishing:**
   ```bash
   mosquitto_sub -h <BROKER_IP> -t "homeassistant/sensor/#" -v
   ```
2. **Pair in AirGuard UI:**
   - Select **MQTT Broker** in Device Pairing Wizard.
   - Provide broker IP, port, and credentials.
   - Confirm discovery config parses automatically.
3. **Warm-Up & Calibration Observation:**
   - BME688 MOX sensors require a 5–15 minute heater stabilization period upon boot.
   - Confirm AirGuard UI flags sensor status as `WARMING_UP` during initial boot before transitioning to `CALIBRATED`.

---

## 4. Hardware Verification Status Summary

| Device Family | Hardware Protocol | Integration Status | Physical Lab Verified? |
|---|---|---|---|
| **AirGradient ONE** | Local HTTP REST | Implemented | Mock-tested (Spec verified) |
| **Home Assistant Fan** | REST Service Call | Implemented | Mock-tested (API verified) |
| **ESPHome BME688** | MQTT JSON | Implemented | Tested via in-process MQTT fixture |
| **Simulated HEPA Purifier** | Python Engine | Implemented | **Verified in Test Suite & UI** |

