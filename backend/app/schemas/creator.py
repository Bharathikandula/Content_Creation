from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class CreatorBase(BaseModel):
    email: EmailStr
    name: str
    language: str = "en"
    default_tone: str = "casual"


class CreatorCreate(CreatorBase):
    password: str


class CreatorUpdate(BaseModel):
    name: Optional[str] = None
    language: Optional[str] = None
    default_tone: Optional[str] = None
    affiliate_id: Optional[str] = None


class CreatorResponse(CreatorBase):
    id: int
    affiliate_id: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class VoiceSampleCreate(BaseModel):
    language: str
    text: str


class VoiceSampleResponse(VoiceSampleCreate):
    id: int
    creator_id: int

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None