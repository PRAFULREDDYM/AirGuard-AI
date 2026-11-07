"""AirGuard AI — Consent & Permission Management Router

Provides versioned, auditable consent records for:
- Environmental telemetry access (TELEMETRY_ACCESS)
- Automatic device control (DEVICE_CONTROL)
- Push notifications (PUSH_NOTIFICATIONS)
- Cloud processing (CLOUD_PROCESSING)
- AI model training data sharing (AI_TRAINING_SHARE - strictly unbundled)

Enforces server-side permission checks and automatic cascade revocation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Dict, Any, Optional
from datetime import datetime

from services.api.database import get_db
from services.api.models import User, UserConsent, Home, Device, AuditLog
from services.api.schemas import ConsentCreate, ConsentResponse
from services.api.security import get_current_user

router = APIRouter(prefix="/consents", tags=["Consents & Permissions"])

@router.get("", response_model=List[ConsentResponse])
async def list_user_consents(
    permission_type: Optional[str] = None,
    active_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lists all versioned consent records for the authenticated user."""
    query = select(UserConsent).where(UserConsent.user_id == current_user.id)
    if permission_type:
        query = query.where(UserConsent.permission_type == permission_type)
    if active_only:
        query = query.where(UserConsent.is_active == True, UserConsent.revoked_at == None)

    query = query.order_by(UserConsent.created_at.desc())
    res = await db.execute(query)
    consents = res.scalars().all()
    return [ConsentResponse.model_validate(c) for c in consents]

@router.post("", response_model=ConsentResponse)
async def grant_consent(
    consent_in: ConsentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Grants and records a new versioned consent.
    Deactivates any previous active consent for the same permission_type and scope.
    """
    # Deactivate prior active consent of the same type to maintain clean versioning
    prior_stmt = select(UserConsent).where(
        UserConsent.user_id == current_user.id,
        UserConsent.permission_type == consent_in.permission_type,
        UserConsent.is_active == True
    )
    if consent_in.device_id:
        prior_stmt = prior_stmt.where(UserConsent.device_id == consent_in.device_id)

    prior_res = await db.execute(prior_stmt)
    for prior in prior_res.scalars().all():
        prior.is_active = False

    new_consent = UserConsent(
        user_id=current_user.id,
        home_id=consent_in.home_id,
        device_id=consent_in.device_id,
        integration_scope=consent_in.integration_scope,
        permission_type=consent_in.permission_type,
        authorized_actions=consent_in.authorized_actions,
        consent_version=consent_in.consent_version,
        consent_origin=consent_in.consent_origin,
        is_active=True,
        created_at=datetime.utcnow()
    )
    db.add(new_consent)

    # If granting DEVICE_CONTROL for a specific device, authorize that device
    if consent_in.permission_type == "DEVICE_CONTROL" and consent_in.device_id:
        dev_res = await db.execute(select(Device).where(Device.id == consent_in.device_id))
        dev = dev_res.scalars().first()
        if dev:
            dev.automation_authorized = True

    audit = AuditLog(
        user_id=current_user.id,
        action="CONSENT_GRANTED",
        details={
            "permission_type": consent_in.permission_type,
            "version": consent_in.consent_version,
            "origin": consent_in.consent_origin,
            "device_id": consent_in.device_id
        }
    )
    db.add(audit)

    await db.commit()
    await db.refresh(new_consent)
    return ConsentResponse.model_validate(new_consent)

@router.patch("/{consent_id}/revoke", response_model=ConsentResponse)
async def revoke_consent(
    consent_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Revokes an active consent immediately.
    Server-side enforcement ensures revoked permissions immediately stop future actions.
    If DEVICE_CONTROL is revoked, active device automation permissions are suspended.
    """
    res = await db.execute(
        select(UserConsent).where(UserConsent.id == consent_id, UserConsent.user_id == current_user.id)
    )
    consent = res.scalars().first()
    if not consent:
        raise HTTPException(status_code=404, detail="Consent record not found.")

    consent.is_active = False
    consent.revoked_at = datetime.utcnow()

    # Cascade revoke on devices if DEVICE_CONTROL is revoked
    if consent.permission_type == "DEVICE_CONTROL":
        if consent.device_id:
            dev_res = await db.execute(select(Device).where(Device.id == consent.device_id))
            dev = dev_res.scalars().first()
            if dev:
                dev.automation_authorized = False
        else:
            # Revoked home-wide, disable on all devices in the home
            if consent.home_id:
                devs_res = await db.execute(select(Device).where(Device.home_id == consent.home_id))
                for d in devs_res.scalars().all():
                    d.automation_authorized = False

    audit = AuditLog(
        user_id=current_user.id,
        action="CONSENT_REVOKED",
        details={
            "consent_id": consent.id,
            "permission_type": consent.permission_type,
            "revoked_at": consent.revoked_at.isoformat()
        }
    )
    db.add(audit)

    await db.commit()
    await db.refresh(consent)
    return ConsentResponse.model_validate(consent)

@router.get("/status")
async def get_consent_status_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns a dictionary summarizing active consents for all permission types."""
    res = await db.execute(
        select(UserConsent).where(
            UserConsent.user_id == current_user.id,
            UserConsent.is_active == True,
            UserConsent.revoked_at == None
        )
    )
    active_consents = res.scalars().all()

    types = {
        "TELEMETRY_ACCESS": False,
        "DEVICE_CONTROL": False,
        "PUSH_NOTIFICATIONS": False,
        "CLOUD_PROCESSING": False,
        "AI_TRAINING_SHARE": False
    }

    for c in active_consents:
        if c.permission_type in types:
            types[c.permission_type] = True

    return {
        "active_consents": types,
        "total_active": len(active_consents),
        "timestamp": datetime.utcnow().isoformat()
    }
