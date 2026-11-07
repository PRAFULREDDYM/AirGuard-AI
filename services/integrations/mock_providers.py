"""Mock Provider Servers for Home Assistant and AirGradient.

Provides high-fidelity, deterministic simulated endpoints conforming to the
official API contracts of Home Assistant REST API and AirGradient Local Server API.
Used for end-to-end integration testing, zero-configuration local demos,
and automated validation of consumer pairing and device actuation workflows.
"""

from fastapi import APIRouter, Header, HTTPException, status, Request
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

mock_router = APIRouter(prefix="/mock-providers", tags=["Mock Providers"])

# -----------------------------------------------------------------------------
# In-Memory State for Mock Home Assistant
# -----------------------------------------------------------------------------
MOCK_HA_TOKEN = "mock_ha_secret_token_123"

_ha_state_store: Dict[str, Dict[str, Any]] = {
    "fan.levoit_core_400s": {
        "entity_id": "fan.levoit_core_400s",
        "state": "on",
        "attributes": {
            "friendly_name": "Living Room Levoit Core 400S",
            "percentage": 50,
            "percentage_step": 25.0,
            "speed_list": ["low", "medium", "high", "turbo"],
            "preset_modes": ["sleep", "auto", "manual"],
            "preset_mode": "manual",
            "device_class": "fan",
            "model": "Core 400S",
            "manufacturer": "Levoit / VeSync"
        },
        "last_changed": datetime.utcnow().isoformat(),
        "last_updated": datetime.utcnow().isoformat(),
    },
    "fan.xiaomi_air_purifier_4": {
        "entity_id": "fan.xiaomi_air_purifier_4",
        "state": "off",
        "attributes": {
            "friendly_name": "Bedroom Xiaomi Air Purifier 4",
            "percentage": 0,
            "preset_modes": ["auto", "silent", "favorite"],
            "preset_mode": "auto",
            "device_class": "fan",
            "model": "Smart Air Purifier 4 (zhimi.airp.mb5)",
            "manufacturer": "Xiaomi / Smartmi"
        },
        "last_changed": datetime.utcnow().isoformat(),
        "last_updated": datetime.utcnow().isoformat(),
    },
    "sensor.levoit_core_400s_pm25": {
        "entity_id": "sensor.levoit_core_400s_pm25",
        "state": "14.2",
        "attributes": {
            "friendly_name": "Levoit Core 400S PM2.5",
            "unit_of_measurement": "µg/m³",
            "device_class": "pm25",
            "state_class": "measurement"
        },
        "last_changed": datetime.utcnow().isoformat(),
        "last_updated": datetime.utcnow().isoformat(),
    },
    "sensor.airgradient_living_room_pm25": {
        "entity_id": "sensor.airgradient_living_room_pm25",
        "state": "8.5",
        "attributes": {
            "friendly_name": "AirGradient ONE PM2.5",
            "unit_of_measurement": "µg/m³",
            "device_class": "pm25",
            "state_class": "measurement"
        },
        "last_changed": datetime.utcnow().isoformat(),
        "last_updated": datetime.utcnow().isoformat(),
    },
    "sensor.airgradient_living_room_co2": {
        "entity_id": "sensor.airgradient_living_room_co2",
        "state": "540",
        "attributes": {
            "friendly_name": "AirGradient ONE CO2",
            "unit_of_measurement": "ppm",
            "device_class": "carbon_dioxide",
            "state_class": "measurement"
        },
        "last_changed": datetime.utcnow().isoformat(),
        "last_updated": datetime.utcnow().isoformat(),
    },
    "sensor.airgradient_living_room_tvoc": {
        "entity_id": "sensor.airgradient_living_room_tvoc",
        "state": "120",
        "attributes": {
            "friendly_name": "AirGradient ONE TVOC Index",
            "unit_of_measurement": "index",
            "device_class": "volatile_organic_compounds",
            "state_class": "measurement"
        },
        "last_changed": datetime.utcnow().isoformat(),
        "last_updated": datetime.utcnow().isoformat(),
    }
}

_ha_service_history: List[Dict[str, Any]] = []

def _verify_ha_auth(authorization: Optional[str]):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Missing or invalid Authorization header."
        )
    token = authorization.split("Bearer ")[1].strip()
    if token != MOCK_HA_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid Home Assistant access token."
        )

# -----------------------------------------------------------------------------
# Mock Home Assistant API Endpoints
# -----------------------------------------------------------------------------
@mock_router.get("/ha/api/")
async def mock_ha_root(authorization: Optional[str] = Header(None)):
    """Simulates Home Assistant GET /api/ ping/auth endpoint."""
    _verify_ha_auth(authorization)
    return {"message": "API running."}

@mock_router.get("/ha/api/states")
async def mock_ha_get_states(authorization: Optional[str] = Header(None)):
    """Simulates Home Assistant GET /api/states entity list."""
    _verify_ha_auth(authorization)
    return list(_ha_state_store.values())

@mock_router.get("/ha/api/states/{entity_id}")
async def mock_ha_get_entity_state(entity_id: str, authorization: Optional[str] = Header(None)):
    """Simulates Home Assistant GET /api/states/<entity_id>."""
    _verify_ha_auth(authorization)
    if entity_id not in _ha_state_store:
        raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found.")
    return _ha_state_store[entity_id]

@mock_router.post("/ha/api/services/{domain}/{service}")
async def mock_ha_call_service(
    domain: str,
    service: str,
    payload: Dict[str, Any],
    authorization: Optional[str] = Header(None)
):
    """Simulates Home Assistant service calls (e.g. fan.turn_on, fan.set_percentage)."""
    _verify_ha_auth(authorization)
    entity_id = payload.get("entity_id")
    if not entity_id or entity_id not in _ha_state_store:
        raise HTTPException(status_code=404, detail=f"Target entity '{entity_id}' not found.")

    record = {
        "domain": domain,
        "service": service,
        "payload": payload,
        "timestamp": datetime.utcnow().isoformat()
    }
    _ha_service_history.append(record)

    entity = _ha_state_store[entity_id]
    if domain == "fan":
        if service == "turn_on":
            entity["state"] = "on"
            if entity["attributes"].get("percentage", 0) == 0:
                entity["attributes"]["percentage"] = 50
        elif service == "turn_off":
            entity["state"] = "off"
            entity["attributes"]["percentage"] = 0
        elif service == "set_percentage":
            pct = payload.get("percentage", 50)
            entity["attributes"]["percentage"] = pct
            entity["state"] = "on" if pct > 0 else "off"

    entity["last_changed"] = datetime.utcnow().isoformat()
    entity["last_updated"] = datetime.utcnow().isoformat()

    return [entity]

@mock_router.get("/ha/debug/history")
async def mock_ha_get_history():
    """Returns history of dispatched service calls for testing verification."""
    return {"service_history": _ha_service_history}

@mock_router.post("/ha/debug/reset")
async def mock_ha_reset():
    """Resets mock HA state to defaults."""
    _ha_service_history.clear()
    _ha_state_store["fan.levoit_core_400s"]["state"] = "on"
    _ha_state_store["fan.levoit_core_400s"]["attributes"]["percentage"] = 50
    _ha_state_store["fan.xiaomi_air_purifier_4"]["state"] = "off"
    _ha_state_store["fan.xiaomi_air_purifier_4"]["attributes"]["percentage"] = 0
    return {"message": "Mock HA state reset successfully."}

# -----------------------------------------------------------------------------
# Mock AirGradient Local Server API Endpoints
# -----------------------------------------------------------------------------
_airgradient_state = {
    "serialno": "84fce612984a",
    "model": "I-9PSL",
    "firmware": "3.1.4",
    "rco2": 528,
    "pm01": 4,
    "pm02": 9,
    "pm10": 13,
    "pm02Compensated": 8.7,
    "pm003_count": 760,
    "tvocIndex": 115,
    "tvoc_index": 115,
    "noxIndex": 1,
    "nox_index": 1,
    "atmp": 21.8,
    "atmpCompensated": 21.6,
    "rhum": 47.5,
    "rhumCompensated": 46.8,
    "boot": 1820,
    "wifi": -62
}

@mock_router.get("/airgradient/measures/current")
async def mock_airgradient_measures():
    """Simulates AirGradient ONE Local Server API GET /measures/current."""
    return _airgradient_state

@mock_router.post("/airgradient/debug/update")
async def mock_airgradient_update(data: Dict[str, Any]):
    """Allows test fixtures to set dynamic sensor values."""
    _airgradient_state.update(data)
    return {"status": "updated", "current": _airgradient_state}

