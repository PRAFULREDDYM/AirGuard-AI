# AirGuard AI — Real-Device Validation Status & Connectivity Matrix

## Executive Summary

To preserve scientific and operational honesty, AirGuard AI explicitly distinguishes between:
1. **Physically Verified**: Tested against physical hardware in hand.
2. **Provider-Tested**: Tested against official manufacturer REST/WebSocket/MQTT protocols and contract mocks.
3. **Mock-Tested**: Tested against synthetic state drivers for automated unit/integration CI testing.
4. **Unsupported / Blocked**: Devices that lack local APIs or require closed proprietary cloud protocols.

---

## 1. Supported Integration Pathways & Detailed Model Matrix

| Brand & Model | Connection Route | Telemetry Supported | Controllable Actions | Verification Status | Real Hardware Required? |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Home Assistant (Instance)** | Route A (WebSocket/REST) | Any HA sensor (`sensor.*`) | Fan speeds, Power toggle | **Provider-Tested** | Yes, local HA instance on LAN |
| **Levoit Core 400S** | Via Home Assistant (`fan.levoit_core_400s`) | None (Purifier only) | Fan Speed (1-3, Turbo), Sleep | **Provider-Tested** | Tested via HA integration contract |
| **Levoit Core 300S / 600S** | Via Home Assistant | None (Purifier only) | Fan Speed, Power | **Provider-Tested** | Tested via HA integration contract |
| **AirGradient ONE (v3.1)** | Route B (Direct Local REST `/measures/current`) | PM0.3, PM1.0, PM2.5, PM10, CO2, VOC, NOx, Temp, RH | None (Monitor-only) | **Provider-Tested** | Tested via official Local API schema |
| **AirGradient Open Air** | Route B (Direct Local REST) | PM0.3, PM1.0, PM2.5, PM10, Temp, RH | None (Monitor-only) | **Provider-Tested** | Tested via official Local API schema |
| **Xiaomi Smart Air Purifier 4** | Route B (Local miIO token) | PM2.5, Temp, Humidity | Speed (1-3), Auto, Sleep | **Mock-Tested** | Physical device requires miIO token extraction |
| **ESPHome BME688 Sensor Node** | Route C (MQTT Topic Stream) | 10-step gas resistance, VOC Index, Temp, RH | None (Sensor-only) | **Mock-Tested** | Requires ESP32 + BME688 hardware |
| **SafePurifier HEPA (Simulated)** | Simulation Adapter | PM2.5, PM10, VOC | Speed (1-4), Power, Override | **Physically Verified (Software Emulation)** | Fully self-contained |

---

## 2. Unsupported / Incompatible Hardware Warnings

- **Dyson Pure Cool / Hot+Cool:**
  - *Status:* **Blocked / Cloud Only.**
  - *Reason:* Dyson deprecates local MQTT on modern firmware; modern models mandate cloud AWS IoT tokens.
  - *Guidance:* Consumers are advised to bridge Dyson purifiers into Home Assistant first.
- **Honeywell / Winix Basic HEPA:**
  - *Status:* **Mechanical Switch Only.**
  - *Reason:* No digital network capability. Can only be controlled via external smart plug in power toggle mode (not variable speed).
- **Tuya / Smart Life Purifiers:**
  - *Status:* **Cloud Dependent.**
  - *Reason:* Requires Tuya developer portal token rotation every 6 months. Not suitable for zero-configuration consumer beta.

---

## 3. Failure Mode & Connection Edge Cases Tested

| Test Scenario | Implementation | Test Assertion | Result |
| :--- | :--- | :--- | :--- |
| **Invalid HA Token** | `test_home_assistant_adapter_lifecycle_and_invalid_credentials` | HTTP 401 Unauthorized, Connection Rejected | **PASSED** |
| **Unreachable Device IP** | `test_airgradient_local_adapter_telemetry_and_unreachable` | Socket Timeout, Returns `is_connected=False` | **PASSED** |
| **Cross-Home IDOR Attack** | `test_cross_home_idor_isolation` | User B commanding User A device returns HTTP 403 | **PASSED** |
| **Disconnection & Reconnection** | `test_device_lifecycle_management` | Marks `is_online=False`, refresh re-establishes | **PASSED** |

