# AirGuard AI — Model-Specific Device Compatibility Matrix (Phase 7)

## 1. Executive Summary & Philosophy

AirGuard AI connects existing consumer air purifiers, air-quality monitoring stations, and custom multi-gas electronic noses into an unified, intelligent environmental automation network.

In accordance with AirGuard AI Engineering & Safety Standards:
- **Never claim a device is supported merely because its manufacturer name appears in a brochure.**
- **Never present an unverified network beacon as an authenticated, controllable device.**
- **Strict separation of capabilities:** Tier 1 (Actuation / Fan Control), Tier 2 (Air-Quality Monitoring), and Tier 3 (Advanced Odor Recognition with MOX Gas Sensors). Ordinary purifiers and particulate monitors are never labeled as odor-classifying instruments.

---

## 2. Comprehensive Model-Specific Compatibility Matrix

| Brand & Model | Integration Protocol | API Nature | HA Required? | Cloud vs. Local | Auth Method | Available Telemetry | Available Controls | Verification Level |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Levoit Core 200S** | Home Assistant / VeSync Cloud | Community Integration (pyvesync) | Recommended (HA VeSync) | Cloud (VeSync REST) | VeSync Account (AES-256 token) | None (Filter life % only) | Power, Speed (1-3), Sleep mode, Display toggle | Official Contract Mock-Verified |
| **Levoit Core 300S** | Home Assistant / VeSync Cloud | Community Integration (pyvesync) | Recommended (HA VeSync) | Cloud (VeSync REST) | VeSync Account (AES-256 token) | PM2.5 (Infrared estimate) | Power, Speed (1-4), Auto, Sleep, Child Lock | Official Contract Mock-Verified |
| **Levoit Core 400S** | Home Assistant / VeSync Cloud | Community Integration (pyvesync) | Recommended (HA VeSync) | Cloud (VeSync REST) | VeSync Account (AES-256 token) | PM2.5 (Laser particle count) | Power, Speed (1-4), Auto, Sleep, Display, Timer | Physical & Mock-Verified |
| **Levoit Core 600S** | Home Assistant / VeSync Cloud | Community Integration (pyvesync) | Recommended (HA VeSync) | Cloud (VeSync REST) | VeSync Account (AES-256 token) | PM2.5 (Laser particle count) | Power, Speed (1-5), Auto, Sleep, Display | Official Contract Mock-Verified |
| **Xiaomi Smart Air Purifier 4** | Home Assistant miIO / python-miio | Reverse-Engineered Local (miIO / MiOT) | Optional (Direct local UDP or HA) | 100% Local (Direct LAN) | 32-Char Hex Device Token | PM2.5, Temperature, Humidity, Filter % | Power, Speed/Level (1-3), Auto, Silent, Favorite | Physical & Mock-Verified |
| **Xiaomi Smart Air Purifier 4 Pro** | Home Assistant miIO / python-miio | Reverse-Engineered Local (miIO / MiOT) | Optional (Direct local UDP or HA) | 100% Local (Direct LAN) | 32-Char Hex Device Token | PM2.5, PM10, Temperature, Humidity | Power, Fan Speed, Auto, Night, Favorite | Official Contract Mock-Verified |
| **Xiaomi Smart Air Purifier 4 Compact** | Home Assistant miIO / python-miio | Reverse-Engineered Local (miIO / MiOT) | Optional (Direct local UDP or HA) | 100% Local (Direct LAN) | 32-Char Hex Device Token | PM2.5 | Power, Speed (1-3), Silent, Favorite | Official Contract Mock-Verified |
| **Xiaomi Air Purifier 3H** | Home Assistant miIO / python-miio | Reverse-Engineered Local (miIO / MiOT) | Optional (Direct local UDP or HA) | 100% Local (Direct LAN) | 32-Char Hex Device Token | PM2.5, Temp, Humidity, Filter % | Power, Speed (1-3), Auto, Silent, Favorite | Physical & Mock-Verified |
| **AirGradient ONE (I-9PSL)** | Direct Local REST (`/measures/current`) | Official Manufacturer Local API | No (Direct Local) | 100% Local (LAN HTTP) | Local HTTP (No token required on LAN) | PM1, PM2.5, PM10, CO2 (NDIR), VOC Index, NOx, Temp, Humidity | None (Read-Only Sensor Station) | Physical & Mock-Verified |
| **AirGradient Open Air (O-1PST)** | Direct Local REST (`/measures/current`) | Official Manufacturer Local API | No (Direct Local) | 100% Local (LAN HTTP) | Local HTTP (No token required on LAN) | PM1, PM2.5, PM10, Temp, Humidity | None (Read-Only Sensor Station) | Official Contract Mock-Verified |
| **AirGuard Sensor Node (BME688 + SGP41)** | Direct Local REST / ESPHome API / MQTT | Native AirGuard Open Firmware | No (Native Protocol) | 100% Local (Sub-15ms LAN) | TLS / MQTT Auth / Pre-shared Key | Multi-Gas Resistance (MOX 10-step), VOC Index, NOx, PM2.5, Temp, Hum, Press | Status LED, Heater Profile Selection | Native Hardware Baseline |
| **Coway Airmega 250S / 400S** | Home Assistant IOCare | Community Integration | Required | Cloud (Coway API) | Coway IoCare Account | PM2.5, Air Quality Index (1-4) | Power, Speed (1-3), Smart Mode, Sleep, Light | Community Adapter Tested |
| **Philips 1000i / 2000i / 3000i** | Home Assistant CoAP / pyairctrl | Community Reverse-Engineered (CoAP) | Recommended | 100% Local (CoAP / HTTP) | None / Encrypted CoAP Handshake | PM2.5, Gas/IAI Index (1-12) | Power, Speed (1-3), Auto, Sleep, Turbo | Community Adapter Tested |
| **IKEA Starkvind (Table & Standalone)** | Zigbee2MQTT / Home Assistant ZHA | Official Zigbee 3.0 Cluster Specification | Required (Zigbee Hub) | 100% Local (Zigbee mesh) | Zigbee Network Key (Handled by Coordinator) | PM2.5 | Power, Fan Speed (Auto or 1-9), Child Lock | Official Spec & Mock-Verified |
| **Awair Element** | Local REST API (`/air-data/latest`) | Official Manufacturer Local API | No (Direct Local) | 100% Local (LAN HTTP) | Local HTTP Bearer Token | PM2.5, CO2 (NDIR), TVOC (ppb), Temp, Hum | None (Read-Only Sensor Station) | Official Contract Mock-Verified |
| **PurpleAir Classic / PA-II** | Local JSON API (`/json`) | Official Local Web Server API | No (Direct Local) | 100% Local (LAN HTTP) | None (Local LAN) | Dual Laser PM1, PM2.5, PM10, Temp, Hum, Press | None (Read-Only Sensor Station) | Official Contract Mock-Verified |

---

## 3. Tiered Operational Capability Definition

To eliminate consumer confusion and ensure absolute safety compliance:

### Tier 1: Basic Actuation & Filtration Control
- **Target Hardware:** Smart air purifiers (Levoit, Xiaomi, Coway, Philips, IKEA Starkvind).
- **Functions:** Power state, discrete fan speed, automated mode selection, speed stepping.
- **Safety Enforcement:** Conservative Emergency Suspension (`EMERGENCY_SUSPENDED`) halts ordinary automated speed adjustments upon detected fire, smoke, combustible gas, or certified alarm triggers.

### Tier 2: Precision Air-Quality Monitoring
- **Target Hardware:** Dedicated laser particle counters and NDIR monitors (AirGradient ONE, Awair, PurpleAir).
- **Functions:** Real-time PM2.5, PM10, direct NDIR CO2 (never estimated eCO2), relative VOC/NOx indices, temperature, humidity.
- **Provenances:** Rigorously flagged as `MEASURED` with calibration status and freshness windows.

### Tier 3: Advanced Odor-Pattern Recognition (E-Nose)
- **Target Hardware:** AirGuard Hardware Sensor Node / BME688 MOX multi-gas resistance sensor array.
- **Functions:** 10-step temperature-ramped gas resistance timeseries, session-grouped electronic-nose inference, odor descriptor classification (sweet, fruity, solvent, sulfurous, burnt, etc.).
- **Strict Limitation:** Ordinary air purifiers lacking heated MOX gas sensors are explicitly labeled **"Tier 3 Odor AI Not Available on this hardware"**. Odor predictions are never fabricated from standard PM2.5 or VOC index readings.

