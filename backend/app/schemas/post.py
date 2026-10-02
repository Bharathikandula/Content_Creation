from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PostCreate(BaseModel):
    language: str = "en"
    tone: str = "casual"


class PhotoResponse(BaseModel):
    id: int
    storage_key: str
    expires_at: datetime
    show_on_page: bool

    class Config:
        from_attributes = True


class CaptionVersionResponse(BaseModel):
    id: int
    version: int
    text: str
    hashtags: Optional[List[str]] = None
    outfit_description: Optional[str] = None
    alt_text: Optional[str] = None
    child_present: bool = False

    class Config:
        from_attributes = True


class ProductResponse(BaseModel):
    id: int
    source: str
    title: str
    price: Optional[str] = None
    image_url: Optional[str] = None
    merchant_url: Optional[str] = None
    google_url: Optional[str] = None

    class Config:
        from_attributes = True


class PostProductResponse(BaseModel):
    id: int
    product: Optional[ProductResponse] = None
    affiliate_url: Optional[str] = None
    position: int
    is_generic_idea: bool = False
    generic_idea_text: Optional[str] = None

    class Config:
        from_attributes = True


class CreatorPageResponse(BaseModel):
    id: int
    slug: str
    show_photo: bool
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScriptResponse(BaseModel):
    id: int
    duration_seconds: int
    text: str
    disclosure: Optional[str] = None
    word_count: int

    class Config:
        from_attributes = True


class PostResponse(BaseModel):
    id: int
    creator_id: int
    language: str
    tone: str
    status: str
    created_at: datetime
    photos: List[PhotoResponse] = []
    caption_versions: List[CaptionVersionResponse] = []
    products: List[PostProductResponse] = []
    creator_page: Optional[CreatorPageResponse] = None
    script: Optional[ScriptResponse] = None

    class Config:
        from_attributes = True


class GenerateCaptionRequest(BaseModel):
    post_id: int
    regenerate: bool = False


class GenerateScriptRequest(BaseModel):
    post_id: int
    duration_seconds: int = 30


class CreateCreatorPageRequest(BaseModel):
    post_id: int
    show_photo: bool = False
    expires_in_days: Optional[int] = None