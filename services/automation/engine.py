import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from services.api.models import (
    AutomationRule, AutomationExecution, Device, SensorReading,
    MeasurementType, EventSeverity
)
from services.automation.safety import SafetyEngine
from services.ingestion.service import ws_manager

class AutomationEngine:
    @staticmethod
    async def evaluate_rules_for_reading(
        db: AsyncSession,
        reading: SensorReading,
        device_adapter_dispatcher=None
    ) -> List[AutomationExecution]:
        """
        Evaluates active automation rules when a new sensor reading arrives.
        Executes permitted actions and logs execution records.
        """
        # Get device to know the room/home
        dev_res = await db.execute(select(Device).where(Device.id == reading.device_id))
        source_device = dev_res.scalars().first()
        if not source_device:
            return []

        # Find enabled rules for this home/room and measurement type
        rules_res = await db.execute(
            select(AutomationRule).where(
                AutomationRule.home_id == source_device.home_id,
                AutomationRule.enabled == True
            )
        )
        rules = rules_res.scalars().all()
        executions = []

        now = datetime.utcnow()

        for rule in rules:
            # Check room match if rule is room-scoped
            if rule.room_id and source_device.room_id and rule.room_id != source_device.room_id:
                continue

            trigger = rule.trigger_config
            m_type = trigger.get("measurement_type")
            if m_type != reading.measurement_type.value:
                continue

            # Evaluate condition
            condition = trigger.get("condition", "ABOVE")
            threshold = float(trigger.get("threshold", 0.0))
            is_triggered = False

            if condition == "ABOVE" and reading.value > threshold:
                is_triggered = True
            elif condition == "BELOW" and reading.value < threshold:
                is_triggered = True
            elif condition == "EQUALS" and reading.value == threshold:
                is_triggered = True

            if not is_triggered:
                continue

            # Check cooldown
            if rule.last_triggered_at:
                elapsed = (now - rule.last_triggered_at).total_seconds()
                if elapsed < rule.cooldown_seconds:
                    # Cooldown active, skip execution
                    continue

            # Check rate limit (max executions per hour)
            one_hour_ago = now - timedelta(hours=1)
            exec_count_res = await db.execute(
                select(AutomationExecution).where(
                    AutomationExecution.rule_id == rule.id,
                    AutomationExecution.triggered_at >= one_hour_ago,
                    AutomationExecution.status == "SUCCESS"
                )
            )
            recent_execs = len(exec_count_res.scalars().all())
            if recent_execs >= rule.max_executions_per_hour:
                continue

            # Target device
            action = rule.action_config
            target_device_id = action.get("device_id")
            command = action.get("command", "set_speed")
            params = action.get("parameters", {})

            target_dev_res = await db.execute(
                select(Device).where(Device.id == target_device_id)
            )
            target_device = target_dev_res.scalars().first()
            if not target_device:
                exec_record = AutomationExecution(
                    rule_id=rule.id,
                    device_id=target_device_id or "unknown",
                    command=command,
                    parameters=params,
                    status="FAILED",
                    reason="Target actuator device not found."
                )
                db.add(exec_record)
                continue

            # SAFETY VALIDATION
            is_allowed, safety_reason = SafetyEngine.validate_automation_action(
                device=target_device,
                command=command,
                parameters=params
            )

            if not is_allowed:
                exec_record = AutomationExecution(
                    rule_id=rule.id,
                    device_id=target_device.id,
                    command=command,
                    parameters=params,
                    status="BLOCKED_BY_SAFETY",
                    reason=safety_reason
                )
                db.add(exec_record)
                executions.append(exec_record)
                continue

            # Execute device command
            exec_status = "SUCCESS"
            exec_reason = f"Rule '{rule.name}' triggered on {m_type}={reading.value} {reading.unit}."
            
            if device_adapter_dispatcher:
                try:
                    await device_adapter_dispatcher(target_device, command, params)
                except Exception as e:
                    exec_status = "FAILED"
                    exec_reason = f"Adapter dispatch error: {str(e)}"

            rule.last_triggered_at = now

            exec_record = AutomationExecution(
                rule_id=rule.id,
                device_id=target_device.id,
                command=command,
                parameters=params,
                status=exec_status,
                reason=exec_reason,
                triggered_at=now
            )
            db.add(exec_record)
            executions.append(exec_record)

            # Broadcast execution
            await ws_manager.broadcast({
                "type": "automation_executed",
                "data": {
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "device_id": target_device.id,
                    "device_name": target_device.name,
                    "command": command,
                    "status": exec_status,
                    "reason": exec_reason,
                    "triggered_at": now.isoformat()
                }
            })

        if executions:
            await db.commit()

        return executions

