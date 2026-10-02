from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
import uuid

from ..core.database import get_async_session
from ..models.creator import Creator
from ..models.post import Post, CreatorPage, PostProduct, Photo
from ..schemas.post import CreateCreatorPageRequest, CreatorPageResponse
from ..api.auth import get_current_user

router = APIRouter(prefix="/pages", tags=["pages"])


@router.post("/", response_model=CreatorPageResponse)
async def create_creator_page(
    request: CreateCreatorPageRequest,
    current_user: Creator = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    # Verify post ownership
    result = await session.execute(
        select(Post).where(
            Post.id == request.post_id,
            Post.creator_id == current_user.id,
        )
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Check if page already exists
    existing = await session.execute(
        select(CreatorPage).where(CreatorPage.post_id == request.post_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Creator page already exists for this post")

    # Generate unique slug
    slug = f"{current_user.name.lower().replace(' ', '-')}-{uuid.uuid4().hex[:8]}"

    # Calculate expiry
    expires_at = None
    if request.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days)

    page = CreatorPage(
        post_id=request.post_id,
        slug=slug,
        show_photo=request.show_photo,
        expires_at=expires_at,
    )
    session.add(page)
    await session.commit()
    await session.refresh(page)
    return page


@router.get("/{slug}")
async def get_creator_page(
    slug: str,
    session: AsyncSession = Depends(get_async_session),
):
    # Load page with post and products
    result = await session.execute(
        select(CreatorPage)
        .where(CreatorPage.slug == slug, CreatorPage.deleted == False)
        .options(
            selectinload(CreatorPage.post).selectinload(Post.creator),
            selectinload(CreatorPage.post).selectinload(Post.products).selectinload(PostProduct.product),
            selectinload(CreatorPage.post).selectinload(Post.photos),
            selectinload(CreatorPage.post).selectinload(Post.caption_versions),
        )
    )
    page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    # Check expiry
    if page.expires_at and page.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Page has expired")

    post = page.post
    creator = post.creator

    # Get latest caption
    latest_caption = None
    if post.caption_versions:
        latest_caption = max(post.caption_versions, key=lambda cv: cv.version)

    # Get products
    products = []
    for pp in post.products:
        if pp.is_generic_idea:
            products.append({
                "type": "generic_idea",
                "text": pp.generic_idea_text,
                "position": pp.position,
            })
        elif pp.product:
            products.append({
                "type": "product",
                "title": pp.product.title,
                "price": pp.product.price,
                "image_url": pp.product.image_url,
                "affiliate_url": pp.affiliate_url,
                "source": pp.product.source,
                "position": pp.position,
            })

    # Get photo if allowed
    photo_url = None
    if page.show_photo and post.photos:
        photo_url = post.photos[0].storage_key  # Would need S3 presigned URL

    return {
        "page": {
            "slug": page.slug,
            "show_photo": page.show_photo,
        },
        "creator": {
            "name": creator.name,
        },
        "post": {
            "caption": latest_caption.text if latest_caption else "",
            "outfit_description": latest_caption.outfit_description if latest_caption else "",
            "alt_text": latest_caption.alt_text if latest_caption else "",
            "hashtags": latest_caption.hashtags if latest_caption else [],
        },
        "products": products,
        "photo_url": photo_url,
    }


@router.delete("/{page_id}")
async def delete_creator_page(
    page_id: int,
    current_user: Creator = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        select(CreatorPage)
        .join(Post)
        .where(
            CreatorPage.id == page_id,
            Post.creator_id == current_user.id,
        )
    )
    page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    page.deleted = True
    await session.commit()
    return {"status": "deleted"}