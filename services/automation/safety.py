from datetime import datetime
from typing import Tuple, Optional
from services.api.models import Device, EventSeverity, Home, UserConsent

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
        suspected_hazard: Optional[str] = None,
        home: Optional[Home] = None,
        consent: Optional[UserConsent] = None,
        reading_timestamp: Optional[datetime] = None,
        trigger_measurement_type: Optional[str] = None,
        sensor_room_id: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Validates whether a proposed automation action satisfies all 14 safety invariants:
        1. Prohibits hazardous ozone activation.
        2. Prohibits overriding or disabling certified life-safety alarms.
        3. Enforces conservative emergency suspension on fire/smoke/combustible gas.
        4. Halts on certified life-safety alarm active.
        5. Verifies global home automation pause kill-switch.
        6. Verifies explicit active user consent for device control.
        7. Verifies device automation authorization flag.
        8. Respects manual overrides.
        9. Restricts automatic purifier control to particulate filtration (PM2.5), disallowing unvalidated VOC/odor actuation.
        10. Verifies sensor data freshness (rejects stale readings >120s old).
        11. Verifies sensor and purifier room assignment match.
        12. Verifies device is an actuator, not a read-only monitoring sensor.
        13. Verifies device supports the target command.
        """
        cmd_lower = command.strip().lower()

        # Invariant 1: Never activate ozone generators
        if cmd_lower in SafetyEngine.PROHIBITED_COMMANDS or "ozone" in cmd_lower:
            return False, "SAFETY VIOLATION: Ozone generators are hazardous respiratory irritants and strictly prohibited."

        # Invariant 2: Never disable alarms or override certified safety systems
        if "disable" in cmd_lower and "alarm" in cmd_lower:
            return False, "SAFETY VIOLATION: Disabling certified safety alarms is prohibited."

        # Invariant 3: Conservative Emergency State: Suspend ordinary automation during fire or combustible gas
        # Blanket electrical actuation is avoided to prevent relay contact sparks (ignition hazard)
        # or fan-induced smoke dispersion. Certified equipment operates independently.
        if suspected_hazard in ["gas_leak", "combustible_gas", "fire", "smoke"]:
            return False, (
                f"SAFETY VIOLATION / EMERGENCY SUSPENDED: Automated switching suspended due to suspected {suspected_hazard}. "
                "Ordinary device control halted to eliminate spark ignition hazards and leave certified life-safety systems unhindered."
            )

        # Invariant 4: Certified life-safety alarm active
        if current_event_severity == EventSeverity.CERTIFIED_ALARM:
            return False, (
                "SAFETY VIOLATION / EMERGENCY SUSPENDED: Certified life-safety alarm active. "
                "Automated device actuation suspended; follow building evacuation protocols."
            )

        # Invariant 5: Global Pause Kill Switch
        if home and getattr(home, "automations_paused", False):
            return False, "AUTOMATIONS PAUSED: All automations are paused via the home-wide emergency kill switch."

        # Invariant 6: Consent check
        if consent is not None:
            if not consent.is_active or consent.revoked_at is not None:
                return False, "CONSENT REVOKED: User consent for automatic device control has been revoked."
            if consent.expires_at and consent.expires_at < datetime.utcnow():
                return False, "CONSENT EXPIRED: User consent for automatic device control has expired."

        # Invariant 7: Device automation authorization
        if not device.automation_authorized:
            return False, f"DEVICE BLOCKED: User has not authorized automated control for device '{device.name}'."

        # Invariant 8: Check manual override
        if device.manual_override:
            if device.manual_override_until and device.manual_override_until > datetime.utcnow():
                return False, f"MANUAL OVERRIDE: User manual override active on '{device.name}' until {device.manual_override_until.isoformat()}."
            elif not device.manual_override_until:
                return False, f"MANUAL OVERRIDE: User manual override is currently active on '{device.name}'."

        # Invariant 9: Restrict automatic purifier control to particulate filtration (PM2.5/PM10)
        # Never automatically actuate purifiers from unvalidated odor classifications or generic VOC indices
        if trigger_measurement_type and trigger_measurement_type not in ["PM25", "PM10", "PM1"]:
            return False, (
                f"SAFETY VIOLATION: Automated purifier control is restricted to particulate filtration (PM2.5/PM10). "
                f"Actuation triggered by '{trigger_measurement_type}' is prohibited without clinical/chemical assay."
            )

        # Invariant 10: Telemetry freshness check (reject stale data)
        if reading_timestamp:
            age_seconds = (datetime.utcnow() - reading_timestamp).total_seconds()
            if age_seconds > 120:
                return False, f"STALE SENSOR DATA: Sensor reading is {int(age_seconds)}s old. Automatic commands suspended until fresh telemetry arrives."

        # Invariant 11: Sensor-to-purifier room assignment match
        if sensor_room_id and device.room_id and sensor_room_id != device.room_id:
            return False, "ROOM MISMATCH: Environmental sensor and purifier must belong to the same room for automated pairing."

        # Invariant 12: Device must be a controllable actuator
        if not device.is_controllable:
            return False, f"CAPABILITY ERROR: Device '{device.name}' is a read-only monitoring sensor, not a controllable actuator."

        # Invariant 13: Command must be supported in capability manifest
        if device.capabilities and device.capabilities.controls:
            supported = []
            for c in device.capabilities.controls:
                if isinstance(c, dict):
                    supported.append(c.get("command", "").lower())
                elif isinstance(c, str):
                    supported.append(c.lower())
            if supported and cmd_lower not in supported:
                return False, f"UNSUPPORTED COMMAND: Device '{device.name}' does not support command '{command}'."

        return True, "Safety checks passed."

