from datetime import datetime
from typing import Tuple, Optional
from services.api.models import Device, EventSeverity

class SafetyEngine:
    PROHIBITED_COMMANDS = {
        "turn_on_ozone",
        "activate_ozone",
        "disable_alarm",
        "silence_alarm",
        "override_smoke_alarm",
        "override_co_alarm"
    }

    @staticmethod
    def validate_automation_action(
        device: Device,
        command: str,
        parameters: dict,
        current_event_severity: Optional[EventSeverity] = None,
        suspected_hazard: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Validates whether a proposed automation action is safe according to non-negotiable safety rules.
        Replaces blanket electrical actuation with a conservative emergency state that suspends
        ordinary automation during hazards and leaves certified safety equipment under intended controls.
        Returns: (is_allowed: bool, reason: str)
        """
        cmd_lower = command.strip().lower()

        # Rule 6: Never activate ozone generators
        if cmd_lower in SafetyEngine.PROHIBITED_COMMANDS or "ozone" in cmd_lower:
            return False, "SAFETY VIOLATION: Ozone generators are hazardous respiratory irritants and strictly prohibited."

        # Rule 7: Never disable alarms or override certified safety systems
        if "disable" in cmd_lower and "alarm" in cmd_lower:
            return False, "SAFETY VIOLATION: Disabling certified safety alarms is prohibited."

        # Rule 5: Conservative Emergency State: Suspend ordinary automation during fire or combustible gas
        # Blanket electrical actuation is avoided to prevent relay contact sparks (ignition hazard)
        # or fan-induced smoke dispersion. Certified equipment operates independently.
        if suspected_hazard in ["gas_leak", "combustible_gas", "fire", "smoke"]:
            return False, (
                f"SAFETY VIOLATION / EMERGENCY SUSPENDED: Automated switching suspended due to suspected {suspected_hazard}. "
                "Ordinary device control halted to eliminate spark ignition hazards and leave certified life-safety systems unhindered."
            )

        if current_event_severity == EventSeverity.CERTIFIED_ALARM:
            return False, (
                "SAFETY VIOLATION / EMERGENCY SUSPENDED: Certified life-safety alarm active. "
                "Automated device actuation suspended; follow building evacuation protocols."
            )

        # Check device authorization
        if not device.automation_authorized:
            return False, f"DEVICE BLOCKED: User has not authorized automated control for device '{device.name}'."

        # Check manual override
        if device.manual_override:
            if device.manual_override_until and device.manual_override_until > datetime.utcnow():
                return False, f"MANUAL OVERRIDE: User manual override active on '{device.name}' until {device.manual_override_until.isoformat()}."
            elif not device.manual_override_until:
                return False, f"MANUAL OVERRIDE: User manual override is currently active on '{device.name}'."

        # Check device capability
        if not device.is_controllable:
            return False, f"CAPABILITY ERROR: Device '{device.name}' is a read-only monitoring sensor, not a controllable actuator."

        return True, "Safety checks passed."

