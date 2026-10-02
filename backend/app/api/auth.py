from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Optional

from ..core.config import settings
from ..core.database import get_async_session
from ..models.creator import Creator
from ..schemas.creator import CreatorCreate, CreatorResponse, Token

router = APIRouter(prefix="/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session),
) -> Creator:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await session.execute(select(Creator).where(Creator.email == email))
    creator = result.scalar_one_or_none()

    if creator is None:
        raise credentials_exception
    return creator


@router.post("/register", response_model=CreatorResponse)
async def register(
    creator_data: CreatorCreate,
    session: AsyncSession = Depends(get_async_session),
):
    # Check if email exists
    result = await session.execute(select(Creator).where(Creator.email == creator_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    creator = Creator(
        email=creator_data.email,
        name=creator_data.name,
        hashed_password=get_password_hash(creator_data.password),
        language=creator_data.language,
        default_tone=creator_data.default_tone,
    )
    session.add(creator)
    await session.commit()
    await session.refresh(creator)
    return creator


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(select(Creator).where(Creator.email == form_data.username))
    creator = result.scalar_one_or_none()

    if not creator or not verify_password(form_data.password, creator.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": creator.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=CreatorResponse)
async def get_me(current_user: Creator = Depends(get_current_user)):
    return current_user