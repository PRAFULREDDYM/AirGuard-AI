---
name: safety-automation
description: >-
  Guide for environmental event policies, connected-device control, manual overrides,
  hazardous-condition exclusions, notification decisions, and automation safety constraints.
---

# Safety & Automation Skill

## Purpose
Ensure all automation actions are safe, authorized, audited, and respect hardware limitations.

## Event Classification Hierarchy

| Level | Name | Source | Action |
|-------|------|--------|--------|
| 1 | Normal | Measurements within thresholds | Monitor |
| 2 | Elevated | Threshold exceeded | Alert + optional automation |
| 3 | Anomaly | ML anomaly score high | Alert + investigate |
| 4 | Classified | Trained model confident | Alert + contextual action |
| 5 | Unknown | Unrecognized pattern | Alert + caution |
| 6 | Certified Alarm | Independent safety device | Emergency notification |
| 7 | Sensor Unavailable | No valid readings | Degrade gracefully |

## Automation Rule Structure

```python
class AutomationRule(BaseModel):
    id: UUID
    name: str
    enabled: bool
    trigger_measurement: MeasurementType
    trigger_condition: Condition  # ABOVE, BELOW, CHANGE_RATE
    trigger_threshold: float
    trigger_duration_seconds: int  # Must stay triggered for this long
    hysteresis: float             # Buffer to prevent flapping
    target_device_id: str
    target_action: DeviceCommand
    cooldown_seconds: int         # Min time between executions
    requires_user_permission: bool  # Default True
    room_id: str | None
    max_executions_per_hour: int  # Rate limit
    manual_override_active: bool
```

## Mandatory Safety Constraints

### NEVER automate for:
- Suspected gas leaks → WARN ONLY, never activate electrical equipment
- Fire/smoke events → WARN ONLY, do not control HVAC
- CO alarm events → WARN ONLY, guide to evacuate
- Unknown hazardous conditions → WARN ONLY

### ALWAYS require:
- User explicitly enables automation per device
- Capability verification: device supports the command
- Rate limiting: max 1 command per device per 30 seconds (default)
- Cooldown: configurable minimum between automation cycles
- Manual override: user can always override; automation must respect it
- Audit log: every command recorded with timestamp, trigger, result

## Notification Decision Tree

1. Life-safety event → Immediate push + in-app alert + persistent banner
2. Elevated reading → In-app alert + optional push (user-configured)
3. Anomaly detected → In-app event log + optional notification
4. Automation executed → In-app log + optional notification
5. Device offline → In-app warning after grace period
6. Model untrained → Informational in settings

## Validation Checklist

- [ ] Life-safety events never trigger device automation
- [ ] Manual override prevents automation re-engagement until cleared
- [ ] Rate limiting prevents command flooding
- [ ] Cooldown prevents oscillation
- [ ] Every command is audit-logged
- [ ] Disconnected devices don't receive queued commands silently
- [ ] Notifications distinguish severity levels visually
- [ ] Simulated events are labeled and don't trigger real device commands

