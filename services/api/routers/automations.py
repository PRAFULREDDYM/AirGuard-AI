from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from services.api.database import get_db
from services.api.models import AutomationRule, AutomationExecution, Home, User
from services.api.schemas import (
    AutomationRuleCreate, AutomationRuleUpdate, AutomationRuleResponse,
    AutomationExecutionResponse
)
from services.api.security import get_current_user

router = APIRouter(prefix="/automations", tags=["Automations"])

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

