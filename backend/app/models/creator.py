from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class Creator(Base, TimestampMixin):
    __tablename__ = "creators"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    language = Column(String(10), default="en", nullable=False)
    default_tone = Column(String(50), default="casual")
    affiliate_id = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    voice_samples = relationship("VoiceSample", back_populates="creator", cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="creator", cascade="all, delete-orphan")
    affiliate_accounts = relationship("AffiliateAccount", back_populates="creator", cascade="all, delete-orphan")


class VoiceSample(Base, TimestampMixin):
    __tablename__ = "voice_samples"

    id = Column(Integer, primary_key=True, autoincrement=True)
    creator_id = Column(Integer, ForeignKey("creators.id", ondelete="CASCADE"), nullable=False)
    language = Column(String(10), nullable=False)
    text = Column(Text, nullable=False)

    creator = relationship("Creator", back_populates="voice_samples")


class AffiliateAccount(Base, TimestampMixin):
    __tablename__ = "affiliate_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    creator_id = Column(Integer, ForeignKey("creators.id", ondelete="CASCADE"), nullable=False)
    network = Column(String(100), nullable=False)
    credential = Column(Text, nullable=True)  # Encrypted
    is_default = Column(Boolean, default=False)

    creator = relationship("Creator", back_populates="affiliate_accounts")