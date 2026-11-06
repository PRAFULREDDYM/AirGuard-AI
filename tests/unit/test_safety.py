import pytest
from datetime import datetime, timedelta
from services.api.models import Device, IntegrationType, EventSeverity
from services.automation.safety import SafetyEngine

def test_ozone_generator_strictly_prohibited():
    device = Device(
        name="Living Room Purifier",
        is_controllable=True,
        automation_authorized=True,
        connection_protocol=IntegrationType.SIMULATION
    )
    is_allowed, reason = SafetyEngine.validate_automation_action(
        device=device,
        command="activate_ozone",
        parameters={}
    )
    assert not is_allowed
    assert "Ozone generators are hazardous respiratory irritants" in reason

def test_combustible_gas_leak_blocks_fans_and_switches():
    device = Device(
        name="Ventilation Fan",
        is_controllable=True,
        automation_authorized=True,
        connection_protocol=IntegrationType.HOME_ASSISTANT
    )
    is_allowed, reason = SafetyEngine.validate_automation_action(
        device=device,
        command="set_speed",
        parameters={"speed": "high"},
        suspected_hazard="combustible_gas"
    )
    assert not is_allowed
    assert "combustible_gas" in reason
    assert "SAFETY VIOLATION" in reason

def test_certified_alarm_blocks_automated_fan_control():
    device = Device(
        name="Smart Purifier",
        is_controllable=True,
        automation_authorized=True,
        connection_protocol=IntegrationType.SIMULATION
    )
    is_allowed, reason = SafetyEngine.validate_automation_action(
        device=device,
        command="turn_on",
        parameters={},
        current_event_severity=EventSeverity.CERTIFIED_ALARM
    )
    assert not is_allowed
    assert "Certified life-safety alarm active" in reason

def test_manual_override_respected():
    device = Device(
        name="Bedroom Purifier",
        is_controllable=True,
        automation_authorized=True,
        manual_override=True,
        manual_override_until=datetime.utcnow() + timedelta(minutes=30),
        connection_protocol=IntegrationType.SIMULATION
    )
    is_allowed, reason = SafetyEngine.validate_automation_action(
        device=device,
        command="set_speed",
        parameters={"speed": "low"}
    )
    assert not is_allowed
    assert "MANUAL OVERRIDE" in reason

def test_unauthorized_device_blocks_automation():
    device = Device(
        name="Unpaired Purifier",
        is_controllable=True,
        automation_authorized=False,  # User did not grant permission
        connection_protocol=IntegrationType.SIMULATION
    )
    is_allowed, reason = SafetyEngine.validate_automation_action(
        device=device,
        command="set_speed",
        parameters={"speed": "high"}
    )
    assert not is_allowed
    assert "User has not authorized automated control" in reason

def test_valid_safe_purifier_command_allowed():
    device = Device(
        name="Authorized HEPA Purifier",
        is_controllable=True,
        automation_authorized=True,
        manual_override=False,
        connection_protocol=IntegrationType.SIMULATION
    )
    is_allowed, reason = SafetyEngine.validate_automation_action(
        device=device,
        command="set_speed",
        parameters={"speed": "high"}
    )
    assert is_allowed
    assert "Safety checks passed" in reason

