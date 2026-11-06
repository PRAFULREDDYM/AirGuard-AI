from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import timedelta

from services.api.database import get_db
from services.api.config import settings
from services.api.models import User, Home, Room, Device, DeviceCapability, IntegrationType
from services.api.schemas import UserCreate, UserLogin, UserResponse, Token
from services.api.security import (
    verify_password, get_password_hash, create_access_token, get_current_user
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=Token)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if user already exists
    existing = await db.execute(select(User).where(User.email == user_in.email))
    if existing.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )

    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Automatically create a default Home and Room for new user
    default_home = Home(name="My Home", owner_id=user.id)
    db.add(default_home)
    await db.commit()
    await db.refresh(default_home)

    default_room = Room(home_id=default_home.id, name="Living Room", room_type="living_room")
    db.add(default_room)
    await db.commit()

    token = create_access_token(data={"sub": user.id, "email": user.email})
    return Token(access_token=token, user=UserResponse.model_validate(user))

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalars().first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(data={"sub": user.id, "email": user.email})
    return Token(access_token=token, user=UserResponse.model_validate(user))

@router.post("/demo-login", response_model=Token)
async def demo_login(db: AsyncSession = Depends(get_db)):
    """Creates or logs into a seeded demo account for immediate testing."""
    if settings.ENVIRONMENT.lower() == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo auto-login is disabled in production environments."
        )
    demo_email = "demo@airguard.ai"
    result = await db.execute(select(User).where(User.email == demo_email))
    user = result.scalars().first()

    if not user:
        user = User(
            email=demo_email,
            hashed_password=get_password_hash("airguard123"),
            full_name="Demo User"
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        # Seed Home & Rooms
        home = Home(name="Smart Residence", owner_id=user.id)
        db.add(home)
        await db.commit()
        await db.refresh(home)

        living_room = Room(home_id=home.id, name="Living Room", room_type="living_room", floor=1)
        kitchen = Room(home_id=home.id, name="Kitchen", room_type="kitchen", floor=1)
        bedroom = Room(home_id=home.id, name="Master Bedroom", room_type="bedroom", floor=2)
        db.add_all([living_room, kitchen, bedroom])
        await db.commit()
        await db.refresh(living_room)
        await db.refresh(kitchen)

        # Seed initial simulated devices
        sim_monitor = Device(
            home_id=home.id,
            room_id=living_room.id,
            name="AirGradient ONE (Simulated)",
            manufacturer="AirGradient",
            model="ONE v3.1",
            connection_protocol=IntegrationType.SIMULATION,
            is_controllable=False,
            is_online=True
        )
        sim_purifier = Device(
            home_id=home.id,
            room_id=living_room.id,
            name="SafePurifier HEPA (Simulated)",
            manufacturer="AirGuard Systems",
            model="CleanAir Pro-400",
            connection_protocol=IntegrationType.SIMULATION,
            is_controllable=True,
            automation_authorized=True,
            is_online=True
        )
        db.add_all([sim_monitor, sim_purifier])
        await db.commit()

    token = create_access_token(data={"sub": user.id, "email": user.email})
    return Token(access_token=token, user=UserResponse.model_validate(user))

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)

