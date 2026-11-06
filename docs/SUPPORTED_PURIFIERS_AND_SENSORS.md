# AirGuard AI — Supported Purifiers & Sensors Directory

**Document Version:** 1.0.0  
**Classification:** Hardware Compatibility Matrix & Specifications  
**Date:** November 2026  

---

## 1. Compatibility Overview

AirGuard AI distinguishes **verified hardware integrations** from speculative or unauthenticated network services. Not every model from a particular brand supports digital automation. Models lacking Wi-Fi or Bluetooth controllers are clearly categorized as **Unsupported**, and users are guided through safe alternative options.

---

## 2. Air Purifiers Compatibility Matrix

| Brand | Model | Support Status | Recommended Route | Supported Controls | Supported Sensors | Notes / Limitations |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Levoit / VeSync** | Core 400S | **Supported** | Route A (Home Assistant) | Power, Fan Speeds 1-4, Sleep, Auto, Display Off, Child Lock | Laser PM2.5 ($\mu\text{g/m}^3$) | Fast DC motor; sub-2s command latency via HA VeSync integration. |
| | Core 300S | **Supported** | Route A (Home Assistant) | Power, Fan Speeds 1-3, Sleep, Auto | Optical PM2.5 | Optical sensor reads lower than laboratory laser monitors in clean air. |
| | Core 600S | **Supported** | Route A (Home Assistant) | Power, Fan Speeds 1-4, Sleep, Auto | Laser PM2.5 | High CADR room purifier; ideal for open living areas. |
| | Vital 100S / 200S | **Supported** | Route A (Home Assistant) | Power, Speeds 1-4, Pet Mode, Light Sensor | Laser PM2.5 | Pet filtration profile supported. |
| | Core 300 (Non-Smart) | **Unsupported** | Route D (Alternatives) | None (Mechanical switch only) | None | **Alternative:** Pair external AirGradient monitor; toggle via certified Zigbee smart plug. |
| | Vista 200 | **Unsupported** | Route D (Alternatives) | None | None | No onboard digital controller. |
| **Xiaomi / Smartmi** | Smart Air Purifier 4 / 4 Pro | **Supported** | Route B (Direct Local) or Route A | Power, Fan Speeds 1-3, Favorite RPM, Auto, Night, OLED Display | Laser PM2.5, Temperature, Humidity | Supports direct local miIO token for 100% cloud-free local control (<20ms). |
| | Air Purifier 3H / 3C | **Supported** | Route B (Direct Local) or Route A | Power, Fan Level, Auto, Sleep | Laser PM2.5, Temp, Humidity | miIO local control verified. |
| | Purifier 1st Gen | **Unsupported** | Route D (Alternatives) | Deprecated | None | Legacy cloud encryption protocol unsupported. |
| **Coway** | Airmega 250S / 300S / 400S | **Supported** | Route A (Home Assistant) | Power, Fan Speeds 1-3, Smart Mode, Sleep, Eco Mode | Optical PM2.5, PM10 | Integrated via Coway IoCare cloud API in Home Assistant. |
| | Airmega AP-1512HH | **Unsupported** | Route D (Alternatives) | None (Physical membrane buttons) | None | Requires physical button press; smart plug power-cycling only. |
| **Philips** | Series 1000i / 2000i / 3000i | **Supported** | Route A (Home Assistant) | Power, Speeds 1-3, Auto, Turbo, Night, Light On/Off | Laser PM2.5, Allergen Index (IAI) | Local CoAP/HTTP protocol supported via HA integration. |
| **Blueair** | Classic 205 / 405 / 605 | **Supported** | Route A (Home Assistant) | Fan Speeds 1-3, Auto Mode, LED Brightness | PM2.5, VOC Index | Requires Blueair Friend Wi-Fi module. |
| | Blue Pure 411 / 211+ | **Unsupported** | Route D (Alternatives) | None | None | Single physical push-button control. |
| **IKEA** | STARKVIND (Table / Floor) | **Supported** | Route A (Home Assistant / Zigbee) | Power, Fan Speeds 1-5, Auto Mode | Optical PM2.5 | Standard Zigbee 3.0 protocol via DIRIGERA or Zigbee2MQTT. |
| | FÖRNUFTIG | **Partial** | Route D (Smart Plug) | On/Off toggle via certified smart plug | None | Mechanical 3-speed rotary knob; leave set to Speed 2. |

---

## 3. Dedicated Air-Quality Monitors

| Brand | Model | Support Status | Protocol | Measurements Provided | Update Rate |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **AirGradient** | ONE v3.1 / v9 | **Native** | Direct Local HTTP / MQTT | Laser PM1.0, PM2.5, PM10; Senseair S8 NDIR $CO_2$; Sensirion SGP40 VOC & NOx; Temp, Humidity | 5–10 seconds |
| | Open Air Outdoor | **Native** | Direct Local HTTP / MQTT | Dual laser PM2.5, Temp, Humidity, Pressure | 10 seconds |
| **Awair** | Awair Element | **Supported** | Local REST API (`/air-data/latest`) | Laser PM2.5, TVOC (ppb), $CO_2$ (ppm), Temp, Humidity | 10 seconds |
| **PurpleAir** | PA-II Indoor / Outdoor | **Supported** | Direct Local JSON (`/json`) | Dual laser Channel A & B cross-validated PM1.0, PM2.5, PM10 | 10–20 seconds |
| **Qingping** | Air Monitor (CGS1) | **Supported** | Home Assistant / miIO | Laser PM2.5, PM10, $CO_2$, Temp, Humidity | 15 seconds |

---

## 4. Custom Electronic-Nose Sensors (AirGuard Sensor Node)

| Hardware | Sensors Onboard | Interface | Machine Learning Application |
| :--- | :--- | :--- | :--- |
| **AirGuard Sensor Node** | Bosch BME688 (4-in-1 MOX gas) + Plantower PMS5003 + Senseair S8 | ESP32-WROOM-32 / I2C / UART / ESPHome / MQTT | 10-step heater scanning ($100^\circ\text{C}–400^\circ\text{C}$); statistical odor pattern classification (coffee, food, ambient baseline). |

---

## 5. Non-Negotiable Safety & Feature Boundaries

1. **Ozone Generation Prohibited:** Any device offering corona discharge or ozone generation (e.g. older ionizers) has ozone controls hard-locked to **OFF** in AirGuard software. Ozone is a toxic pulmonary irritant.
2. **Combustible Gas Safety Rule:** If VOC, gas resistance, or safety sensors detect a suspected explosive gas leak (natural gas/methane, propane), all purifier fans and electrical relays are hard-locked to **OFF/NO-ACTUATION** to prevent spark ignition.
3. **No Medical Claims:** All particulate, gas, and odor metrics are intended for consumer indoor environmental management only, not medical diagnosis or occupational safety certification.
