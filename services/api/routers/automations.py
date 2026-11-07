from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from services.api.database import get_db
from services.api.models import AutomationRule, AutomationExecution, Home, User, Device
from services.api.schemas import (
    AutomationRuleCreate, AutomationRuleUpdate, AutomationRuleResponse,
    AutomationExecutionResponse
)
from services.api.security import get_current_user

router = APIRouter(prefix="/automations", tags=["Automations"])

@router.get("/presets")
async def get_automation_presets():
    """Returns consumer-friendly automation presets with built-in hysteresis and safety limits."""
    return [
        {
            "id": "clean_air_guard",
            "title": "Clean Air Guard (Elevated Particles)",
            "description": "Automatically increases purifier filtration speed when fine particle levels (PM2.5) become elevated.",
            "measurement_used": "PM2.5 concentration (µg/m³)",
            "trigger_condition": "PM2.5 > 25.0 µg/m³ for 2 continuous minutes",
            "hysteresis_recovery": "Returns to Low / Eco mode when PM2.5 drops below 12.0 µg/m³ for 5 minutes",
            "action_performed": "Set purifier fan to Speed 3 (High Filtration)",
            "cooldown_seconds": 1800,  # 30 minutes
            "safety_protections": [
                "Respects physical button manual overrides for 30 minutes",
                "Hard-locked OFF if fire alarm or combustible gas leak is detected",
                "Rate-limited to 1 physical command per 30 seconds"
            ]
        },
        {
            "id": "odor_eliminator",
            "title": "Odor & Chemical Eliminator (VOC Spike)",
            "description": "Boosts carbon filtration when cooking smoke, cleaning solvents, or VOC spikes are detected.",
            "measurement_used": "Sensirion VOC Index / Gas Resistance",
            "trigger_condition": "VOC Index > 200 or significant resistance drop across heating steps",
            "hysteresis_recovery": "Returns to Auto mode when VOC Index returns to normal (< 100)",
            "action_performed": "Boost purifier to Maximum Speed for 20 minutes",
            "cooldown_seconds": 1200,
            "safety_protections": [
                "Never activates fans if fuel gas (natural gas/methane) leak is suspected",
                "Respects manual user overrides"
            ]
        },
        {
            "id": "night_quiet_guard",
            "title": "Nighttime Whisper Mode",
            "description": "Ensures uninterrupted sleep by locking purifier to whisper-quiet Sleep mode overnight.",
            "measurement_used": "Time Schedule (10:00 PM – 7:00 AM)",
            "trigger_condition": "Local time enters night window",
            "hysteresis_recovery": "Resumes normal Clean Air Guard at 7:00 AM",
            "action_performed": "Set purifier mode to Sleep / Speed 1 and dim indicator LEDs",
            "cooldown_seconds": 3600,
            "safety_protections": ["Can be overridden at any time by user"]
        }
    ]

from pydantic import BaseModel
class ApplyPresetRequest(BaseModel):
    home_id: str
    room_id: str
    preset_id: str
    purifier_device_id: str
    sensor_device_id: Optional[str] = None
    mode: str = "auto_control"  # "monitor_only" | "notify_only" | "auto_control"

@router.post("/apply-preset", response_model=AutomationRuleResponse)
async def apply_preset(
    req: ApplyPresetRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Configures a beginner-friendly automation preset between a room sensor and purifier."""
    home_res = await db.execute(select(Home).where(Home.id == req.home_id, Home.owner_id == current_user.id))
    if not home_res.scalars().first():
        raise HTTPException(status_code=404, detail="Home not found.")

    dev_res = await db.execute(select(Device).where(Device.id == req.purifier_device_id))
    purifier = dev_res.scalars().first()
    if not purifier:
        raise HTTPException(status_code=404, detail="Purifier device not found.")

    if not purifier.is_controllable and req.mode == "auto_control":
        raise HTTPException(status_code=400, detail="The selected device is a read-only sensor and cannot be controlled.")

    if req.preset_id == "odor_eliminator" and req.mode == "auto_control":
        raise HTTPException(
            status_code=400,
            detail="SAFETY INVARIANT: Automatic purifier control from unvalidated VOC or odor classifications is prohibited. Use 'notify_only' mode."
        )

    # If auto_control, explicitly authorize device automation and ensure consent
    if req.mode == "auto_control":
        purifier.automation_authorized = True
        from services.api.models import UserConsent
        consent_res = await db.execute(
            select(UserConsent).where(
                UserConsent.user_id == current_user.id,
                UserConsent.permission_type == "DEVICE_CONTROL",
                UserConsent.is_active == True
            )
        )
        if not consent_res.scalars().first():
            new_c = UserConsent(
                user_id=current_user.id,
                home_id=req.home_id,
                device_id=purifier.id,
                permission_type="DEVICE_CONTROL",
                authorized_actions=["fan.set_speed", "fan.turn_on", "fan.turn_off"],
                consent_version="1.0",
                consent_origin="automation_preset",
                is_active=True
            )
            db.add(new_c)
        await db.commit()

    if req.preset_id == "clean_air_guard":
        name = "Clean Air Guard (Auto PM2.5 Control)"
        trigger_config = {
            "type": "pm25_threshold",
            "threshold": 25.0,
            "hysteresis_threshold": 12.0,
            "mode": req.mode,
            "sensor_device_id": req.sensor_device_id
        }
        action_config = {
            "target_device_id": purifier.id,
            "command": "set_speed",
            "parameters": {"speed": 3} if req.mode == "auto_control" else {},
            "recovery_command": "set_speed",
            "recovery_parameters": {"speed": 1} if req.mode == "auto_control" else {},
            "notify_user": req.mode in ("notify_only", "auto_control")
        }
        cooldown = 1800
    elif req.preset_id == "odor_eliminator":
        name = "Odor Eliminator (VOC Spike)"
        trigger_config = {
            "type": "voc_threshold",
            "threshold": 200.0,
            "hysteresis_threshold": 100.0,
            "mode": req.mode,
            "sensor_device_id": req.sensor_device_id
        }
        action_config = {
            "target_device_id": purifier.id,
            "command": "set_speed",
            "parameters": {"speed": 4} if req.mode == "auto_control" else {},
            "recovery_command": "set_speed",
            "recovery_parameters": {"speed": 1} if req.mode == "auto_control" else {},
            "notify_user": req.mode in ("notify_only", "auto_control")
        }
        cooldown = 1200
    else:
        name = "Custom Room Automation"
        trigger_config = {"type": "manual", "mode": req.mode}
        action_config = {"target_device_id": purifier.id, "command": "set_speed", "parameters": {"speed": 2}}
        cooldown = 1800

    rule = AutomationRule(
        home_id=req.home_id,
        room_id=req.room_id,
        name=name,
        enabled=True,
        trigger_config=trigger_config,
        action_config=action_config,
        cooldown_seconds=cooldown,
        max_executions_per_hour=4
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return AutomationRuleResponse.model_validate(rule)

@router.get("", response_model=List[AutomationRuleResponse])
async def list_rules(
    home_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    home_res = await db.execute(select(Home).where(Home.id == home_id, Home.owner_id == current_user.id))
    if not home_res.scalars().first():
        raise HTTPException(status_code=404, detail="Home not found.")

    res = await db.execute(select(AutomationRule).where(AutomationRule.home_id == home_id))
    rules = res.scalars().all()
    return [AutomationRuleResponse.model_validate(r) for r in rules]

@router.post("", response_model=AutomationRuleResponse)
async def create_rule(
    rule_in: AutomationRuleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    home_res = await db.execute(select(Home).where(Home.id == rule_in.home_id, Home.owner_id == current_user.id))
    if not home_res.scalars().first():
        raise HTTPException(status_code=404, detail="Home not found.")

    rule = AutomationRule(
        home_id=rule_in.home_id,
        room_id=rule_in.room_id,
        name=rule_in.name,
        enabled=rule_in.enabled,
        trigger_config=rule_in.trigger_config,
        action_config=rule_in.action_config,
        cooldown_seconds=rule_in.cooldown_seconds,
        max_executions_per_hour=rule_in.max_executions_per_hour
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return AutomationRuleResponse.model_validate(rule)

@router.patch("/{rule_id}", response_model=AutomationRuleResponse)
async def update_rule(
    rule_id: str,
    rule_in: AutomationRuleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(AutomationRule).where(AutomationRule.id == rule_id))
    rule = res.scalars().first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found.")

    if rule_in.name is not None:
        rule.name = rule_in.name
    if rule_in.enabled is not None:
        rule.enabled = rule_in.enabled
    if rule_in.trigger_config is not None:
        rule.trigger_config = rule_in.trigger_config
    if rule_in.action_config is not None:
        rule.action_config = rule_in.action_config
    if rule_in.cooldown_seconds is not None:
        rule.cooldown_seconds = rule_in.cooldown_seconds
    if rule_in.max_executions_per_hour is not None:
        rule.max_executions_per_hour = rule_in.max_executions_per_hour

    await db.commit()
    await db.refresh(rule)
    return AutomationRuleResponse.model_validate(rule)

@router.delete("/{rule_id}")
async def delete_rule(
    rule_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(AutomationRule).where(AutomationRule.id == rule_id))
    rule = res.scalars().first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found.")
    await db.delete(rule)
    await db.commit()
    return {"message": "Rule deleted successfully."}

@router.get("/executions", response_model=List[AutomationExecutionResponse])
async def list_executions(
    rule_id: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    query = select(AutomationExecution)
    if rule_id:
        query = query.where(AutomationExecution.rule_id == rule_id)
    query = query.order_by(AutomationExecution.triggered_at.desc()).limit(limit)

    res = await db.execute(query)
    execs = res.scalars().all()
    return [AutomationExecutionResponse.model_validate(e) for e in execs]

@router.post("/pause-all")
async def pause_all_automations(
    home_id: str,
    paused: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Emergency kill-switch: pauses or resumes all automated device actuation across the home.
    Halts any running automation execution immediately.
    """
    home_res = await db.execute(select(Home).where(Home.id == home_id, Home.owner_id == current_user.id))
    home = home_res.scalars().first()
    if not home:
        raise HTTPException(status_code=404, detail="Home not found.")

    home.automations_paused = paused
    from services.api.models import AuditLog
    audit = AuditLog(
        user_id=current_user.id,
        action="AUTOMATIONS_PAUSED" if paused else "AUTOMATIONS_RESUMED",
        details={"home_id": home.id, "automations_paused": paused}
    )
    db.add(audit)
    await db.commit()

    return {
        "home_id": home.id,
        "automations_paused": home.automations_paused,
        "message": "All AirGuard automations have been paused." if paused else "All AirGuard automations have been resumed."
    }

