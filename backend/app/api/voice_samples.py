from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from ..core.database import get_async_session
from ..models.creator import Creator, VoiceSample
from ..schemas.creator import VoiceSampleCreate, VoiceSampleResponse
from ..api.auth import get_current_user

router = APIRouter(prefix="/voice-samples", tags=["voice_samples"])


@router.post("/", response_model=VoiceSampleResponse)
async def create_voice_sample(
    sample_data: VoiceSampleCreate,
    current_user: Creator = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    # Check limit (10 samples per language)
    result = await session.execute(
        select(VoiceSample)
        .where(VoiceSample.creator_id == current_user.id)
        .where(VoiceSample.language == sample_data.language)
    )
    existing = result.scalars().all()
    if len(existing) >= 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 voice samples per language",
        )

    sample = VoiceSample(
        creator_id=current_user.id,
        language=sample_data.language,
        text=sample_data.text,
    )
    session.add(sample)
    await session.commit()
    await session.refresh(sample)
    return sample


@router.get("/", response_model=List[VoiceSampleResponse])
async def list_voice_samples(
    language: str = None,
    current_user: Creator = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    query = select(VoiceSample).where(VoiceSample.creator_id == current_user.id)
    if language:
        query = query.where(VoiceSample.language == language)

    result = await session.execute(query)
    return result.scalars().all()


@router.delete("/{sample_id}")
async def delete_voice_sample(
    sample_id: int,
    current_user: Creator = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        select(VoiceSample).where(
            VoiceSample.id == sample_id,
            VoiceSample.creator_id == current_user.id,
        )
    )
    sample = result.scalar_one_or_none()
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")

    await session.delete(sample)
    await session.commit()
    return {"status": "deleted"}