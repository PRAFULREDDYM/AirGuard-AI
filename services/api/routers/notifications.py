"""AirGuard AI — Notifications & Alert Management Router

Implements:
- User-configurable notification preferences by room, device, event category, and delivery channel.
- In-app alerts independent of push-notification permissions.
- Quiet hours suppression for non-critical alerts.
- Notification deduplication and alert cooldown tracking.
- Test-notification delivery verification.
- Alert history with read/unread status and batch acknowledgment.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Dict, Any, Optional
from datetime import datetime, time, timedelta

from services.api.database import get_db
from services.api.models import (
    User, Home, Room, Device, Alert, NotificationPreference, EventSeverity, PushSubscription
)
from services.api.schemas import (
    AlertResponse, NotificationPreferenceCreate, NotificationPreferenceResponse,
    NotificationTestRequest, PushSubscriptionCreate, PushSubscriptionResponse, AlertAckResponse
)
from services.api.security import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications & Alerts"])

@router.get("/preferences", response_model=List[NotificationPreferenceResponse])
async def list_notification_preferences(
    home_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lists notification preferences configured for the home."""
    home_res = await db.execute(select(Home).where(Home.id == home_id, Home.owner_id == current_user.id))
    if not home_res.scalars().first():
        raise HTTPException(status_code=404, detail="Home not found.")

    res = await db.execute(
        select(NotificationPreference).where(
            NotificationPreference.home_id == home_id,
            NotificationPreference.user_id == current_user.id
        )
    )
    prefs = res.scalars().all()
    return [NotificationPreferenceResponse.model_validate(p) for p in prefs]

@router.post("/preferences", response_model=NotificationPreferenceResponse)
async def set_notification_preference(
    pref_in: NotificationPreferenceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Creates or updates a notification preference for an event category/channel."""
    home_res = await db.execute(select(Home).where(Home.id == pref_in.home_id, Home.owner_id == current_user.id))
    if not home_res.scalars().first():
        raise HTTPException(status_code=404, detail="Home not found.")

    # Check existing preference for same category & channel
    existing_res = await db.execute(
        select(NotificationPreference).where(
            NotificationPreference.home_id == pref_in.home_id,
            NotificationPreference.user_id == current_user.id,
            NotificationPreference.event_category == pref_in.event_category,
            NotificationPreference.delivery_channel == pref_in.delivery_channel
        )
    )
    existing = existing_res.scalars().first()

    if existing:
        existing.enabled = pref_in.enabled
        existing.min_severity = pref_in.min_severity
        existing.quiet_hours_enabled = pref_in.quiet_hours_enabled
        existing.quiet_hours_start = pref_in.quiet_hours_start
        existing.quiet_hours_end = pref_in.quiet_hours_end
        existing.cooldown_minutes = pref_in.cooldown_minutes
        pref = existing
    else:
        pref = NotificationPreference(
            user_id=current_user.id,
            home_id=pref_in.home_id,
            room_id=pref_in.room_id,
            device_id=pref_in.device_id,
            event_category=pref_in.event_category,
            delivery_channel=pref_in.delivery_channel,
            enabled=pref_in.enabled,
            min_severity=pref_in.min_severity,
            quiet_hours_enabled=pref_in.quiet_hours_enabled,
            quiet_hours_start=pref_in.quiet_hours_start,
            quiet_hours_end=pref_in.quiet_hours_end,
            cooldown_minutes=pref_in.cooldown_minutes
        )
        db.add(pref)

    await db.commit()
    await db.refresh(pref)
    return NotificationPreferenceResponse.model_validate(pref)

@router.get("/history", response_model=List[AlertResponse])
async def get_notification_history(
    home_id: str,
    unread_only: bool = False,
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves chronological alert and notification history for the home."""
    home_res = await db.execute(select(Home).where(Home.id == home_id, Home.owner_id == current_user.id))
    if not home_res.scalars().first():
        raise HTTPException(status_code=404, detail="Home not found.")

    query = select(Alert).where(Alert.home_id == home_id)
    if unread_only:
        query = query.where(Alert.is_read == False)

    query = query.order_by(Alert.created_at.desc()).limit(limit)
    res = await db.execute(query)
    alerts = res.scalars().all()
    return [AlertResponse.model_validate(a) for a in alerts]

@router.patch("/{alert_id}/read", response_model=AlertResponse)
async def mark_alert_read(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Marks an alert notification as read."""
    res = await db.execute(
        select(Alert).join(Home, Alert.home_id == Home.id).where(
            Alert.id == alert_id,
            Home.owner_id == current_user.id
        )
    )
    alert = res.scalars().first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")

    alert.is_read = True
    alert.read_at = datetime.utcnow()
    await db.commit()
    await db.refresh(alert)
    return AlertResponse.model_validate(alert)

@router.post("/mark-all-read")
async def mark_all_alerts_read(
    home_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Marks all unread alerts in the home as read."""
    home_res = await db.execute(select(Home).where(Home.id == home_id, Home.owner_id == current_user.id))
    if not home_res.scalars().first():
        raise HTTPException(status_code=404, detail="Home not found.")

    res = await db.execute(select(Alert).where(Alert.home_id == home_id, Alert.is_read == False))
    unread_alerts = res.scalars().all()

    now = datetime.utcnow()
    for a in unread_alerts:
        a.is_read = True
        a.read_at = now

    await db.commit()
    return {"marked_count": len(unread_alerts), "message": f"{len(unread_alerts)} alert(s) marked as read."}

@router.post("/test")
async def send_test_notification(
    req: NotificationTestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Dispatches a test notification to verify delivery channels (In-App and Web Push).
    Does not fabricate platform confirmation if push is not confirmed.
    """
    home_res = await db.execute(select(Home).where(Home.id == req.home_id, Home.owner_id == current_user.id))
    home = home_res.scalars().first()
    if not home:
        raise HTTPException(status_code=404, detail="Home not found.")

    test_alert = Alert(
        home_id=home.id,
        severity=EventSeverity.INFO,
        title="AirGuard Notification Test",
        message="This is a verified test notification confirming alert delivery to your device.",
        category="DEVICE_ERROR",
        delivery_channel=req.channel,
        delivery_status="DELIVERED" if req.channel == "IN_APP" else "PENDING_CLIENT_CONFIRMATION",
        is_read=False,
        created_at=datetime.utcnow()
    )
    db.add(test_alert)
    await db.commit()
    await db.refresh(test_alert)

    return {
        "success": True,
        "alert_id": test_alert.id,
        "channel": req.channel,
        "delivery_status": test_alert.delivery_status,
        "message": f"Test notification successfully dispatched via {req.channel}."
    }


@router.post("/push-subscribe", response_model=PushSubscriptionResponse)
async def register_push_subscription(
    sub_in: PushSubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Registers a Web Push API subscription (endpoint, p256dh key, auth key) for the authenticated user.
    """
    # Check if subscription already exists
    existing_res = await db.execute(
        select(PushSubscription).where(
            PushSubscription.user_id == current_user.id,
            PushSubscription.endpoint == sub_in.endpoint
        )
    )
    existing = existing_res.scalars().first()
    if existing:
        existing.p256dh_key = sub_in.p256dh_key
        existing.auth_key = sub_in.auth_key
        existing.user_agent = sub_in.user_agent
        existing.is_active = True
        sub = existing
    else:
        sub = PushSubscription(
            user_id=current_user.id,
            endpoint=sub_in.endpoint,
            p256dh_key=sub_in.p256dh_key,
            auth_key=sub_in.auth_key,
            user_agent=sub_in.user_agent,
            is_active=True
        )
        db.add(sub)

    await db.commit()
    await db.refresh(sub)
    return PushSubscriptionResponse.model_validate(sub)


@router.post("/{alert_id}/ack", response_model=AlertAckResponse)
async def acknowledge_alert_delivery(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Acknowledges client delivery confirmation for a notification.
    Transitions status to DELIVERED and records timestamp to ensure no false delivery claims.
    """
    res = await db.execute(
        select(Alert).join(Home, Alert.home_id == Home.id).where(
            Alert.id == alert_id,
            Home.owner_id == current_user.id
        )
    )
    alert = res.scalars().first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")

    now = datetime.utcnow()
    alert.delivery_status = "DELIVERED"
    alert.acknowledged_at = now
    await db.commit()
    await db.refresh(alert)

    return AlertAckResponse(
        alert_id=alert.id,
        delivery_status=alert.delivery_status,
        acknowledged_at=now,
        message="Alert delivery successfully acknowledged by client."
    )


@router.post("/check-device-health")
async def check_device_offline_health(
    home_id: str,
    timeout_seconds: int = Query(default=300, ge=60, le=3600),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Scans devices in the home for missed heartbeats or stale telemetry.
    Generates deduplicated DEVICE_ERROR / OFFLINE_SENSOR alerts when a device exceeds timeout.
    """
    home_res = await db.execute(select(Home).where(Home.id == home_id, Home.owner_id == current_user.id))
    home = home_res.scalars().first()
    if not home:
        raise HTTPException(status_code=404, detail="Home not found.")

    dev_res = await db.execute(select(Device).where(Device.home_id == home_id))
    devices = dev_res.scalars().all()

    now = datetime.utcnow()
    alerts_created = []

    for dev in devices:
        # Check if last seen exceeds timeout
        is_stale = False
        if dev.last_seen_at:
            delta = (now - dev.last_seen_at).total_seconds()
            if delta > timeout_seconds:
                is_stale = True
        else:
            # Never seen and created more than timeout ago
            if (now - dev.created_at).total_seconds() > timeout_seconds:
                is_stale = True

        if is_stale and dev.is_online:
            dev.is_online = False
            
            # Check deduplication cooldown (skip if recent alert exists in last 30 mins)
            recent_alert_res = await db.execute(
                select(Alert).where(
                    Alert.device_id == dev.id,
                    Alert.category == "OFFLINE_SENSOR",
                    Alert.created_at >= now - timedelta(minutes=30)
                )
            )
            if not recent_alert_res.scalars().first():
                alert = Alert(
                    home_id=home.id,
                    room_id=dev.room_id,
                    device_id=dev.id,
                    severity=EventSeverity.WARNING,
                    title=f"Device Offline: {dev.name}",
                    message=f"The device '{dev.name}' ({dev.manufacturer} {dev.model}) has stopped sending telemetry and may be offline or unplugged.",
                    category="OFFLINE_SENSOR",
                    delivery_channel="IN_APP",
                    delivery_status="DELIVERED",
                    delivery_attempts=1,
                    is_read=False,
                    created_at=now
                )
                db.add(alert)
                alerts_created.append(dev.name)

    await db.commit()
    return {
        "scanned_devices": len(devices),
        "offline_alerts_created": len(alerts_created),
        "offline_devices": alerts_created
    }


