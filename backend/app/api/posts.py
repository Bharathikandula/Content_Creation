from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from datetime import datetime, timedelta
import uuid
import boto3
from io import BytesIO

from ..core.config import settings
from ..core.database import get_async_session
from ..models.creator import Creator
from ..models.post import Post, Photo, CaptionVersion, CaptionEvent, Product, PostProduct, CreatorPage, Script
from ..schemas.post import (
    PostCreate, PostResponse, GenerateCaptionRequest,
    GenerateScriptRequest, CreateCreatorPageRequest
)
from ..api.auth import get_current_user

router = APIRouter(prefix="/posts", tags=["posts"])


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name=settings.S3_REGION,
    )


@router.post("/", response_model=PostResponse)
async def create_post(
    post_data: PostCreate,
    current_user: Creator = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    post = Post(
        creator_id=current_user.id,
        language=post_data.language or current_user.language,
        tone=post_data.tone or current_user.default_tone,
        status="draft",
    )
    session.add(post)
    await session.commit()
    await session.refresh(post)
    return post


@router.post("/{post_id}/photo")
async def upload_photo(
    post_id: int,
    file: UploadFile = File(...),
    current_user: Creator = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    # Verify post ownership
    result = await session.execute(
        select(Post).where(Post.id == post_id, Post.creator_id == current_user.id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Upload to S3
    file_key = f"photos/{current_user.id}/{post_id}/{uuid.uuid4()}.jpg"
    s3 = get_s3_client()

    file_data = await file.read()
    s3.upload_fileobj(
        BytesIO(file_data),
        settings.S3_BUCKET_NAME,
        file_key,
        ExtraArgs={"ContentType": file.content_type},
    )

    # Create photo record
    photo = Photo(
        post_id=post_id,
        storage_key=file_key,
        expires_at=datetime.utcnow() + timedelta(hours=settings.PHOTO_EXPIRY_HOURS),
    )
    session.add(photo)
    await session.commit()
    await session.refresh(photo)

    return {"photo_id": photo.id, "storage_key": file_key}


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: int,
    current_user: Creator = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        select(Post)
        .where(Post.id == post_id, Post.creator_id == current_user.id)
        .options(
            selectinload(Post.photos),
            selectinload(Post.caption_versions).selectinload(CaptionVersion.events),
            selectinload(Post.products).selectinload(PostProduct.product),
            selectinload(Post.creator_page),
            selectinload(Post.script),
        )
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.get("/", response_model=List[PostResponse])
async def list_posts(
    current_user: Creator = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        select(Post)
        .where(Post.creator_id == current_user.id)
        .options(
            selectinload(Post.photos),
            selectinload(Post.caption_versions),
            selectinload(Post.products).selectinload(PostProduct.product),
            selectinload(Post.creator_page),
            selectinload(Post.script),
        )
        .order_by(Post.created_at.desc())
    )
    return result.scalars().all()


@router.post("/{post_id}/caption/{version_id}/copy")
async def log_caption_copy(
    post_id: int,
    version_id: int,
    current_user: Creator = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    event = CaptionEvent(caption_version_id=version_id, action="copy")
    session.add(event)
    await session.commit()
    return {"status": "logged"}


@router.post("/{post_id}/caption/{version_id}/regenerate")
async def log_caption_regenerate(
    post_id: int,
    version_id: int,
    current_user: Creator = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    event = CaptionEvent(caption_version_id=version_id, action="regenerate")
    session.add(event)
    await session.commit()
    return {"status": "logged"}