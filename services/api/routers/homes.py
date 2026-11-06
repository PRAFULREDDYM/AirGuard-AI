from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from services.api.database import get_db
from services.api.models import Home, Room, User
from services.api.schemas import HomeCreate, HomeResponse, RoomResponse
from services.api.security import get_current_user

router = APIRouter(prefix="/homes", tags=["Homes"])

@router.get("", response_model=List[HomeResponse])
async def list_homes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Home).where(Home.owner_id == current_user.id))
    homes = result.scalars().all()
    return [HomeResponse.model_validate(h) for h in homes]

@router.post("", response_model=HomeResponse)
async def create_home(
    home_in: HomeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    home = Home(
        name=home_in.name,
        address=home_in.address,
        owner_id=current_user.id
    )
    db.add(home)
    await db.commit()
    await db.refresh(home)
    return HomeResponse.model_validate(home)

@router.get("/{home_id}", response_model=HomeResponse)
async def get_home(
    home_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Home).where(Home.id == home_id, Home.owner_id == current_user.id))
    home = result.scalars().first()
    if not home:
        raise HTTPException(status_code=404, detail="Home not found.")
    return HomeResponse.model_validate(home)

@router.delete("/{home_id}")
async def delete_home(
    home_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Home).where(Home.id == home_id, Home.owner_id == current_user.id))
    home = result.scalars().first()
    if not home:
        raise HTTPException(status_code=404, detail="Home not found.")
    await db.delete(home)
    await db.commit()
    return {"message": "Home deleted successfully."}

