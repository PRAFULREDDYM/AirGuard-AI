from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from services.api.database import get_db
from services.api.models import EnvironmentalEvent, Alert, User, EventSeverity
from services.api.schemas import EventResponse, EventAcknowledge, AlertResponse
from services.api.security import get_current_user

router = APIRouter(prefix="/events", tags=["Events & Alerts"])

@router.get("", response_model=List[EventResponse])
async def list_events(
    room_id: Optional[str] = None,
    severity: Optional[EventSeverity] = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    query = select(EnvironmentalEvent)
    if room_id:
        query = query.where(EnvironmentalEvent.room_id == room_id)
    if severity:
        query = query.where(EnvironmentalEvent.severity == severity)

    query = query.order_by(EnvironmentalEvent.started_at.desc()).limit(limit)
    res = await db.execute(query)
    events = res.scalars().all()
    return [EventResponse.model_validate(e) for e in events]

@router.patch("/{event_id}/acknowledge", response_model=EventResponse)
async def acknowledge_event(
    event_id: str,
    ack_in: EventAcknowledge,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(EnvironmentalEvent).where(EnvironmentalEvent.id == event_id))
    event = res.scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found.")

    event.acknowledged = True
    if ack_in.user_feedback:
        event.user_feedback = ack_in.user_feedback
    await db.commit()
    await db.refresh(event)
    return EventResponse.model_validate(event)

@router.get("/alerts", response_model=List[AlertResponse])
async def list_alerts(
    home_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(Alert)
        .where(Alert.home_id == home_id)
        .order_by(Alert.created_at.desc())
        .limit(50)
    )
    alerts = res.scalars().all()
    return [AlertResponse.model_validate(a) for a in alerts]

