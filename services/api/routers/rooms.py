from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Dict, Any

from services.api.database import get_db
from services.api.models import Room, Home, Device, User
from services.api.schemas import RoomCreate, RoomResponse, DeviceResponse
from services.api.security import get_current_user
from services.ingestion.service import IngestionService

router = APIRouter(prefix="/rooms", tags=["Rooms"])

@router.get("", response_model=List[RoomResponse])
async def list_rooms(
    home_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify home ownership
    home_res = await db.execute(select(Home).where(Home.id == home_id, Home.owner_id == current_user.id))
    if not home_res.scalars().first():
        raise HTTPException(status_code=404, detail="Home not found.")

    res = await db.execute(select(Room).where(Room.home_id == home_id))
    rooms = res.scalars().all()
    return [RoomResponse.model_validate(r) for r in rooms]

@router.post("", response_model=RoomResponse)
async def create_room(
    room_in: RoomCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    home_res = await db.execute(select(Home).where(Home.id == room_in.home_id, Home.owner_id == current_user.id))
    if not home_res.scalars().first():
        raise HTTPException(status_code=404, detail="Home not found.")

    room = Room(
        home_id=room_in.home_id,
        name=room_in.name,
        room_type=room_in.room_type,
        floor=room_in.floor,
        target_pm25=room_in.target_pm25
    )
    db.add(room)
    await db.commit()
    await db.refresh(room)
    return RoomResponse.model_validate(room)

@router.get("/{room_id}")
async def get_room_details(
    room_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Room).where(Room.id == room_id))
    room = res.scalars().first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found.")

    # Get room devices
    dev_res = await db.execute(select(Device).where(Device.room_id == room_id))
    devices = dev_res.scalars().all()

    # Get latest sensor readings
    latest_readings = await IngestionService.get_latest_readings_for_room(db, room_id)

    return {
        "room": RoomResponse.model_validate(room),
        "devices": [DeviceResponse.model_validate(d) for d in devices],
        "latest_readings": latest_readings
    }

@router.delete("/{room_id}")
async def delete_room(
    room_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Room).where(Room.id == room_id))
    room = res.scalars().first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found.")
    await db.delete(room)
    await db.commit()
    return {"message": "Room deleted successfully."}

