"""
AirGuard AI — Device Compatibility & Brand Knowledgebase Catalog
Provides consumer-friendly compatibility search, brand profiles, connection routes,
and detailed capabilities manifests separating SENSORS from CONTROLS.
"""

from fastapi import APIRouter, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

router = APIRouter(prefix="/catalog", tags=["Device Catalog & Compatibility"])

class DeviceModelProfile(BaseModel):
    id: str
    brand: str
    model_name: str
    category: str  # "purifier" | "monitor" | "sensor" | "platform"
    is_supported: bool
    support_tier: str  # "native" | "home_assistant" | "local_api" | "unsupported" | "smart_plug_only"
    recommended_route: str  # "Route A (Home Assistant)" | "Route B (Direct Local)" | "Route C (Manufacturer Cloud)" | "Route D (Unsupported)"
    image_slug: str
    summary: str
    supported_sensors: List[str]
    unsupported_sensors: List[str]
    supported_controls: List[str]
    unsupported_controls: List[str]
    setup_steps: List[str]
    troubleshooting_tips: List[str]
    alternative_options: Optional[List[str]] = None

CATALOG_DATABASE: List[DeviceModelProfile] = [
    # --- AIR PURIFIERS ---
    DeviceModelProfile(
        id="levoit-core-400s",
        brand="Levoit / VeSync",
        model_name="Core 400S Smart Air Purifier",
        category="purifier",
        is_supported=True,
        support_tier="home_assistant",
        recommended_route="Route A (Home Assistant)",
        image_slug="levoit_core400s",
        summary="High-performance HEPA purifier with smart WiFi connectivity, laser PM2.5 sensor, and 4-speed DC motor.",
        supported_sensors=["PM2.5 (Built-in laser)"],
        unsupported_sensors=["PM1.0", "PM10", "CO2", "VOC Index", "NOx", "Electronic-Nose Channels"],
        supported_controls=["Power On/Off", "Fan Speed 1-4", "Sleep Mode", "Auto Mode", "Display Lock", "Filter Lifetime %"],
        unsupported_controls=["Ozone Generation (Prohibited by AirGuard)", "Combustible Gas Actuation"],
        setup_steps=[
            "1. Connect the Core 400S to your 2.4GHz Wi-Fi using the VeSync smartphone app.",
            "2. In Home Assistant, install the official 'VeSync' integration and enter your VeSync credentials.",
            "3. In AirGuard AI, click 'Connect an existing air purifier' → 'Route A: Home Assistant'.",
            "4. Select the 'fan.core_400s' entity to import it into your living room."
        ],
        troubleshooting_tips=[
            "Ensure the purifier is online in the VeSync app before connecting to Home Assistant.",
            "If fan control latency exceeds 3 seconds, verify Home Assistant cloud polling frequency.",
            "Manual button presses on the purifier will trigger AirGuard's 30-minute manual override hold."
        ]
    ),
    DeviceModelProfile(
        id="levoit-core-300s",
        brand="Levoit / VeSync",
        model_name="Core 300S Smart Air Purifier",
        category="purifier",
        is_supported=True,
        support_tier="home_assistant",
        recommended_route="Route A (Home Assistant)",
        image_slug="levoit_core300s",
        summary="Compact bedroom air purifier with Wi-Fi, 3 fan speeds, and quiet sleep mode.",
        supported_sensors=["PM2.5 (Basic optical sensor)"],
        unsupported_sensors=["CO2", "VOC", "Electronic-Nose Channels"],
        supported_controls=["Power On/Off", "Fan Speed 1-3", "Sleep Mode", "Auto Mode", "Display Off"],
        unsupported_controls=["Ozone Generation"],
        setup_steps=[
            "1. Pair with VeSync app over Wi-Fi.",
            "2. Import into Home Assistant via VeSync integration.",
            "3. Pair into AirGuard via Home Assistant or Direct VeSync Token."
        ],
        troubleshooting_tips=[
            "Core 300S optical PM2.5 sensor may read lower than laboratory laser monitors in clean air."
        ]
    ),
    DeviceModelProfile(
        id="levoit-core-300-non-smart",
        brand="Levoit / VeSync",
        model_name="Core 300 (Non-Smart Mechanical)",
        category="purifier",
        is_supported=False,
        support_tier="unsupported",
        recommended_route="Route D (Unsupported)",
        image_slug="levoit_core300",
        summary="Classic mechanical dial air purifier. Has no Wi-Fi, Bluetooth, or digital control interface.",
        supported_sensors=[],
        unsupported_sensors=["All Sensors (No onboard electronics)"],
        supported_controls=[],
        unsupported_controls=["Digital Speed Control", "Power Control"],
        setup_steps=[
            "Direct digital connection is not possible because this unit lacks smart connectivity."
        ],
        troubleshooting_tips=[],
        alternative_options=[
            "Option 1: Pair a separate AirGradient or AirGuard monitor to the room for air quality tracking.",
            "Option 2: Plug the Core 300 into a certified smart plug (e.g. Zigbee or HomeKit plug) set to Speed 2. AirGuard can toggle power safely with a 15-minute minimum cycle time.",
            "Option 3: Follow AirGuard's manual clean-air recommendations displayed on your room card."
        ]
    ),
    DeviceModelProfile(
        id="xiaomi-smart-air-purifier-4",
        brand="Xiaomi / Smartmi",
        model_name="Xiaomi Smart Air Purifier 4 / 4 Pro",
        category="purifier",
        is_supported=True,
        support_tier="local_api",
        recommended_route="Route B (Direct Local) or Route A (Home Assistant)",
        image_slug="xiaomi_purifier4",
        summary="High CADR purifier featuring OLED display, high-precision laser PM2.5, negative ionizer, and local miIO control.",
        supported_sensors=["PM2.5 (Laser particle sensor)", "Temperature", "Relative Humidity"],
        unsupported_sensors=["CO2", "VOC Index", "Electronic-Nose Channels"],
        supported_controls=["Power On/Off", "Fan Speed Level 1-3", "Favorite RPM Level", "Auto Mode", "Night Mode", "OLED Brightness"],
        unsupported_controls=["Ozone Generation"],
        setup_steps=[
            "1. Connect the purifier to your home Wi-Fi via Xiaomi Home app.",
            "2. Retrieve the 32-character miIO local token (via Xiaomi cloud extractor or Home Assistant).",
            "3. In AirGuard AI, select 'Connect an existing air purifier' → 'Route B: Direct Local'.",
            "4. Enter device IP and miIO token for 100% cloud-free, sub-second local control."
        ],
        troubleshooting_tips=[
            "Ensure the purifier has a DHCP reservation or static IP on your local router.",
            "If the miIO token changes after re-pairing in Xiaomi Home, update the token in AirGuard settings."
        ]
    ),
    DeviceModelProfile(
        id="coway-airmega-250s",
        brand="Coway",
        model_name="Coway Airmega 250S / 400S",
        category="purifier",
        is_supported=True,
        support_tier="home_assistant",
        recommended_route="Route A (Home Assistant)",
        image_slug="coway_airmega",
        summary="Medical-grade Green True HEPA air purifier with automated Smart Mode and dual air intake.",
        supported_sensors=["PM2.5 (Optical particle sensor)", "PM10"],
        unsupported_sensors=["CO2", "VOC", "Electronic-Nose Channels"],
        supported_controls=["Power On/Off", "Fan Speed 1-3", "Smart / Auto Mode", "Sleep Mode", "Eco Mode", "Filter Life %"],
        unsupported_controls=["Ozone Generation"],
        setup_steps=[
            "1. Set up in Coway IoCare app.",
            "2. Connect Coway IoCare to Home Assistant using the Home Assistant Coway integration.",
            "3. Import into AirGuard under Home Assistant."
        ],
        troubleshooting_tips=[
            "IoCare servers periodically rate-limit rapid speed changes; AirGuard's 30-second rate limiter protects against lockouts."
        ]
    ),
    DeviceModelProfile(
        id="ikea-starkvind",
        brand="IKEA",
        model_name="IKEA STARKVIND Air Purifier",
        category="purifier",
        is_supported=True,
        support_tier="home_assistant",
        recommended_route="Route A (Home Assistant / Zigbee)",
        image_slug="ikea_starkvind",
        summary="Design-forward table and floor air purifier using standard Zigbee 3.0 protocol.",
        supported_sensors=["PM2.5 (Optical sensor)"],
        unsupported_sensors=["CO2", "VOC", "Electronic-Nose Channels"],
        supported_controls=["Power On/Off", "Fan Speed 1-5", "Auto Mode"],
        unsupported_controls=["Ozone Generation"],
        setup_steps=[
            "1. Pair STARKVIND with DIRIGERA hub or Zigbee2MQTT / ZHA.",
            "2. Connect Home Assistant to AirGuard AI.",
            "3. Select the STARKVIND fan entity."
        ],
        troubleshooting_tips=[
            "Ensure Zigbee mesh signal is strong to prevent packet drops during automatic fan adjustment."
        ]
    ),

    # --- AIR QUALITY MONITORS ---
    DeviceModelProfile(
        id="airgradient-one",
        brand="AirGradient",
        model_name="AirGradient ONE v3.1 / v9",
        category="monitor",
        is_supported=True,
        support_tier="native",
        recommended_route="Route B (Direct Local API)",
        image_slug="airgradient_one",
        summary="Open-hardware indoor air quality monitor with laboratory-grade Senseair S8 NDIR CO2, Plantower PMS5003 PM, and Sensirion SGP40 VOC/NOx.",
        supported_sensors=[
            "PM1.0 (µg/m³)", "PM2.5 (µg/m³)", "PM10 (µg/m³)",
            "Direct NDIR CO2 (ppm)",
            "Sensirion VOC Index (1-500)", "Sensirion NOx Index (1-500)",
            "Ambient Temperature (°C)", "Relative Humidity (%)"
        ],
        unsupported_sensors=["Electronic-Nose Multi-Heater Profiles (Requires AirGuard Sensor Node)"],
        supported_controls=[],
        unsupported_controls=["Actuation Controls (Device is a pure measurement station)"],
        setup_steps=[
            "1. Ensure AirGradient ONE is powered on and connected to your local Wi-Fi.",
            "2. Enable Local Server in the AirGradient device settings (or broadcast mDNS).",
            "3. AirGuard's Local Gateway detects it automatically, or enter its local IP address.",
            "4. Readings immediately stream into the room dashboard every 5 seconds."
        ],
        troubleshooting_tips=[
            "If port 80/9926 fails to respond, verify local server mode is enabled in the AirGradient dashboard.",
            "Sensirion SGP40 VOC index requires a 15-minute rolling baseline upon first boot."
        ]
    ),
    DeviceModelProfile(
        id="awair-element",
        brand="Awair",
        model_name="Awair Element",
        category="monitor",
        is_supported=True,
        support_tier="local_api",
        recommended_route="Route B (Direct Local API) or Route A (Home Assistant)",
        image_slug="awair_element",
        summary="Compact consumer monitor tracking PM2.5, TVOC, CO2, temperature, and humidity with local HTTP API.",
        supported_sensors=["PM2.5", "eCO2 / NDIR CO2", "TVOC (ppb)", "Temperature", "Humidity"],
        unsupported_sensors=["Electronic-Nose Multi-Heater Profiles"],
        supported_controls=[],
        unsupported_controls=["Actuation Controls"],
        setup_steps=[
            "1. Enable Local Sensors feature in Awair smartphone app.",
            "2. Obtain device local IP address.",
            "3. Pair via Route B in AirGuard AI using http://[ip]/air-data/latest."
        ],
        troubleshooting_tips=[
            "Local API requires Awair firmware version 1.3.0 or higher."
        ]
    ),
    DeviceModelProfile(
        id="purpleair-pa-ii",
        brand="PurpleAir",
        model_name="PurpleAir PA-II Indoor / Outdoor",
        category="monitor",
        is_supported=True,
        support_tier="local_api",
        recommended_route="Route B (Direct Local)",
        image_slug="purpleair_paii",
        summary="Dual-laser optical particle counter with continuous cross-validation between Channel A and Channel B.",
        supported_sensors=["PM1.0", "PM2.5 (Dual-Channel Laser)", "PM10", "Temperature", "Humidity", "Atmospheric Pressure"],
        unsupported_sensors=["CO2", "VOC", "Electronic-Nose Channels"],
        supported_controls=[],
        unsupported_controls=["Actuation Controls"],
        setup_steps=[
            "1. Connect PurpleAir to local Wi-Fi.",
            "2. Enter PurpleAir IP in AirGuard Local API connection wizard.",
            "3. Dual-channel readings are averaged and validated against EPA standard calibration curves."
        ],
        troubleshooting_tips=[
            "AirGuard flags readings with sensor drift if Channel A and Channel B diverge by >20%."
        ]
    ),

    # --- AIRGUARD SENSOR NODE ---
    DeviceModelProfile(
        id="airguard-node-bme688",
        brand="AirGuard Systems",
        model_name="AirGuard Sensor Node (BME688 + PMS5003 + S8)",
        category="sensor",
        is_supported=True,
        support_tier="native",
        recommended_route="Route C (AirGuard Easy Setup / Improv / ESPHome)",
        image_slug="airguard_sensor_node",
        summary="Official AI-first environmental electronic nose. Features 10-step high-temperature MOX gas resistance scanning (100°C–400°C) for machine learning odor pattern recognition.",
        supported_sensors=[
            "10-Step Heating Gas Resistance Profile (100°C–400°C)",
            "Sensirion VOC/VSC Electronic Nose Signatures",
            "Plantower Laser PM1.0, PM2.5, PM10 (Optional)",
            "Senseair S8 True NDIR CO2 (Optional)",
            "Barometric Pressure (hPa)", "Ambient Temperature (°C)", "Relative Humidity (%)"
        ],
        unsupported_sensors=[],
        supported_controls=["OTA Firmware Updates", "Sensor Calibration Reset", "Heater Profile Select"],
        unsupported_controls=["Air Filtration (Pair with a supported purifier for room cleanup)"],
        setup_steps=[
            "1. Connect the ESP32 node to USB power.",
            "2. Use WebSerial / Improv Wi-Fi in Chrome or scan the node's QR code on mobile.",
            "3. Select your home Wi-Fi network.",
            "4. Node authenticates and begins streaming 10-step gas resistance vectors into the AI Model Lab."
        ],
        troubleshooting_tips=[
            "First-time use requires a 48-hour burn-in period to stabilize the metal oxide semiconductor.",
            "Allow 15 minutes of warm-up after boot before recording odor classification benchmarks."
        ]
    ),

    # --- SMART HOME PLATFORMS ---
    DeviceModelProfile(
        id="home-assistant-platform",
        brand="Home Assistant",
        model_name="Home Assistant Core / OS (REST & WebSocket Bridge)",
        category="platform",
        is_supported=True,
        support_tier="native",
        recommended_route="Route A (Home Assistant)",
        image_slug="home_assistant",
        summary="Open-source home automation hub bridging thousands of IoT devices, zigbee networks, and smart purifiers directly into AirGuard.",
        supported_sensors=["All mapped HA sensor entities (PM2.5, CO2, VOC, Temp, Hum, Pressure)"],
        unsupported_sensors=[],
        supported_controls=["All mapped HA fan/purifier entities (speed, mode, power)"],
        unsupported_controls=["Combustible gas actuation (Blocked by AirGuard safety engine)"],
        setup_steps=[
            "1. Open Home Assistant → User Profile → Long-Lived Access Tokens → Create Token.",
            "2. In AirGuard, enter Home Assistant URL (e.g. http://homeassistant.local:8123) and paste token.",
            "3. Select which devices AirGuard has permission to read or control."
        ],
        troubleshooting_tips=[
            "Ensure 'Allow API access' is checked in Home Assistant.",
            "Use http:// instead of https:// if Home Assistant is running on local IP without signed SSL."
        ]
    )
]

@router.get("/devices", response_model=List[DeviceModelProfile])
async def search_catalog(
    q: Optional[str] = Query(None, description="Search brand or model name"),
    category: Optional[str] = Query(None, description="Filter by purifier, monitor, sensor, or platform"),
    supported_only: Optional[bool] = Query(None, description="Filter only supported devices")
):
    """Returns curated brand and model profiles with compatibility breakdown."""
    results = CATALOG_DATABASE
    if category:
        results = [d for d in results if d.category == category]
    if supported_only is not None:
        results = [d for d in results if d.is_supported == supported_only]
    if q:
        query = q.lower().strip()
        results = [
            d for d in results
            if query in d.brand.lower() or query in d.model_name.lower() or query in d.summary.lower()
        ]
    return results

@router.get("/devices/{device_id}", response_model=DeviceModelProfile)
async def get_catalog_device(device_id: str):
    for d in CATALOG_DATABASE:
        if d.id == device_id:
            return d
    return CATALOG_DATABASE[0]
