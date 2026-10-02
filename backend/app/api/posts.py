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
from ..models.post import (
    Post, Photo, CaptionVersion, CaptionEvent,
    Product, PostProduct, CreatorPage, Script
)
from ..schemas.post import (
    PostCreate, PostResponse, CaptionVersionResponse,
    GenerateCaptionRequest, GenerateScriptRequest,
    CreateCreatorPageRequest, CreatorPageResponse, ScriptResponse
)
from ..api.auth import get_current_user
from ..graph.pipeline import build_graph, build_script_graph

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


@router.post("/{post_id}/generate")
async def generate_content(
    post_id: int,
    request: GenerateCaptionRequest,
    current_user: Creator = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    # Load post with relationships
    result = await session.execute(
        select(Post)
        .where(Post.id == post_id, Post.creator_id == current_user.id)
        .options(
            selectinload(Post.photos),
            selectinload(Post.caption_versions),
        )
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if not post.photos:
        raise HTTPException(status_code=400, detail="Upload a photo first")

    # Get photo URLs
    s3 = get_s3_client()
    photo_urls = []
    for photo in post.photos:
        url = s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.S3_BUCKET_NAME,
                "Key": photo.storage_key,
            },
            ExpiresIn=3600,
        )
        photo_urls.append(url)

    # Get voice samples
    voice_result = await session.execute(
        select(VoiceSample)
        .where(VoiceSample.creator_id == current_user.id)
        .where(VoiceSample.language == post.language)
    )
    voice_samples = [vs.text for vs in voice_result.scalars().all()]

    # Build initial state
    initial_state = {
        "post_id": post.id,
        "creator_id": current_user.id,
        "language": post.language,
        "tone": post.tone,
        "photo_urls": photo_urls,
        "voice_samples": voice_samples,
        "creator_profile": {
            "name": current_user.name,
            "language": current_user.language,
            "default_tone": current_user.default_tone,
        },
        "outfit_items": [],
        "occasion": "",
        "child_present": False,
        "caption": "",
        "outfit_description": "",
        "alt_text": "",
        "hashtags": [],
        "search_queries": [],
        "candidates": [],
        "selected_products": [],
        "generic_ideas": [],
        "script_text": None,
        "script_duration": None,
        "script_word_count": None,
        "search_attempts": 0,
        "current_version": 0,
        "error": None,
    }

    # Run pipeline
    graph = build_graph()
    result = graph.invoke(initial_state)

    # Save caption version
    version = len(post.caption_versions) + 1 if request.regenerate else 1
    caption_version = CaptionVersion(
        post_id=post.id,
        version=version,
        text=result["caption"],
        hashtags=result["hashtags"],
        outfit_description=result["outfit_description"],
        alt_text=result["alt_text"],
        child_present=result["child_present"],
    )
    session.add(caption_version)

    # Save products
    for i, product_candidate in enumerate(result.get("selected_products", [])):
        # Create or find product
        product = Product(
            source=product_candidate.source,
            title=product_candidate.title,
            price=product_candidate.price,
            image_url=product_candidate.image_url,
            merchant_url=product_candidate.merchant_url,
            google_url=product_candidate.google_url,
            fetched_at=datetime.utcnow(),
        )
        session.add(product)
        await session.flush()

        post_product = PostProduct(
            post_id=post.id,
            product_id=product.id,
            affiliate_url=product_candidate.affiliate_url,
            position=i + 1,
            is_generic_idea=False,
        )
        session.add(post_product)

    # Save generic ideas
    for idea in result.get("generic_ideas", []):
        post_product = PostProduct(
            post_id=post.id,
            product_id=None,
            position=idea.item_index,
            is_generic_idea=True,
            generic_idea_text=idea.text,
        )
        session.add(post_product)

    # Save script if generated
    if result.get("script_text"):
        script = Script(
            post_id=post.id,
            duration_seconds=result.get("script_duration", 30),
            text=result["script_text"],
            disclosure="This post contains affiliate links.",
            word_count=result.get("script_word_count", 0),
        )
        session.add(script)

    post.status = "completed"
    await session.commit()

    # Reload post with relationships
    result = await session.execute(
        select(Post)
        .where(Post.id == post_id)
        .options(
            selectinload(Post.photos),
            selectinload(Post.caption_versions),
            selectinload(Post.products).selectinload(PostProduct.product),
            selectinload(Post.creator_page),
            selectinload(Post.script),
        )
    )
    post = result.scalar_one()
    return post


@router.post("/{post_id}/script")
async def generate_script(
    post_id: int,
    request: GenerateScriptRequest,
    current_user: Creator = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    # Load post
    result = await session.execute(
        select(Post)
        .where(Post.id == post_id, Post.creator_id == current_user.id)
        .options(
            selectinload(Post.products).selectinload(PostProduct.product),
        )
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Build state for script graph
    selected_products = []
    for pp in post.products:
        if pp.product and not pp.is_generic_idea:
            from ..graph.state import ProductCandidate
            selected_products.append(ProductCandidate(
                source=pp.product.source,
                title=pp.product.title,
                price=pp.product.price,
            ))

    initial_state = {
        "post_id": post.id,
        "creator_id": current_user.id,
        "language": post.language,
        "tone": post.tone,
        "outfit_items": [],
        "selected_products": selected_products,
        "script_duration": request.duration_seconds,
        "script_text": None,
        "script_word_count": None,
        "search_attempts": 0,
    }

    # Run script graph
    graph = build_script_graph()
    result = graph.invoke(initial_state)

    # Save script
    existing_script = await session.execute(
        select(Script).where(Script.post_id == post_id)
    )
    existing = existing_script.scalar_one_or_none()

    if existing:
        existing.duration_seconds = request.duration_seconds
        existing.text = result["script_text"]
        existing.word_count = result.get("script_word_count", 0)
    else:
        script = Script(
            post_id=post.id,
            duration_seconds=request.duration_seconds,
            text=result["script_text"],
            disclosure="This post contains affiliate links.",
            word_count=result.get("script_word_count", 0),
        )
        session.add(script)

    await session.commit()

    return {"script": result["script_text"], "word_count": result.get("script_word_count", 0)}


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
    event = CaptionEvent(
        caption_version_id=version_id,
        action="copy",
    )
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
    event = CaptionEvent(
        caption_version_id=version_id,
        action="regenerate",
    )
    session.add(event)
    await session.commit()
    return {"status": "logged"}