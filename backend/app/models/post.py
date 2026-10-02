from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, Float
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class Post(Base, TimestampMixin):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    creator_id = Column(Integer, ForeignKey("creators.id", ondelete="CASCADE"), nullable=False)
    language = Column(String(10), nullable=False)
    tone = Column(String(50), nullable=False)
    status = Column(String(50), default="draft")  # draft, completed, published

    # Relationships
    creator = relationship("Creator", back_populates="posts")
    photos = relationship("Photo", back_populates="post", cascade="all, delete-orphan")
    caption_versions = relationship("CaptionVersion", back_populates="post", cascade="all, delete-orphan")
    products = relationship("PostProduct", back_populates="post", cascade="all, delete-orphan")
    creator_page = relationship("CreatorPage", back_populates="post", uselist=False, cascade="all, delete-orphan")
    script = relationship("Script", back_populates="post", uselist=False, cascade="all, delete-orphan")


class Photo(Base, TimestampMixin):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    storage_key = Column(String(500), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    deleted = Column(Boolean, default=False)
    show_on_page = Column(Boolean, default=False)

    post = relationship("Post", back_populates="photos")


class CaptionVersion(Base, TimestampMixin):
    __tablename__ = "caption_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    hashtags = Column(JSON, nullable=True)
    outfit_description = Column(Text, nullable=True)
    alt_text = Column(Text, nullable=True)
    child_present = Column(Boolean, default=False)

    post = relationship("Post", back_populates="caption_versions")
    events = relationship("CaptionEvent", back_populates="caption_version", cascade="all, delete-orphan")


class CaptionEvent(Base, TimestampMixin):
    __tablename__ = "caption_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    caption_version_id = Column(Integer, ForeignKey("caption_versions.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(50), nullable=False)  # copy, regenerate, thumb_up, thumb_down

    caption_version = relationship("CaptionVersion", back_populates="events")


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(100), nullable=False)
    title = Column(Text, nullable=False)
    price = Column(String(50), nullable=True)
    image_url = Column(Text, nullable=True)
    merchant_url = Column(Text, nullable=True)
    google_url = Column(Text, nullable=True)
    fetched_at = Column(DateTime(timezone=True), nullable=False)


class PostProduct(Base, TimestampMixin):
    __tablename__ = "post_products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    affiliate_url = Column(Text, nullable=True)
    position = Column(Integer, nullable=False)
    is_generic_idea = Column(Boolean, default=False)
    generic_idea_text = Column(Text, nullable=True)

    post = relationship("Post", back_populates="products")
    product = relationship("Product")


class CreatorPage(Base, TimestampMixin):
    __tablename__ = "creator_pages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, unique=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    show_photo = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    deleted = Column(Boolean, default=False)

    post = relationship("Post", back_populates="creator_page")


class Script(Base, TimestampMixin):
    __tablename__ = "scripts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, unique=True)
    duration_seconds = Column(Integer, nullable=False)  # 15, 30, or 45
    text = Column(Text, nullable=False)
    disclosure = Column(Text, nullable=True)
    word_count = Column(Integer, nullable=False)

    post = relationship("Post", back_populates="script")