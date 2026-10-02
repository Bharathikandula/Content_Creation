from typing import TypedDict, List, Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class ProductCandidate:
    source: str
    title: str
    price: Optional[str] = None
    image_url: Optional[str] = None
    merchant_url: Optional[str] = None
    google_url: Optional[str] = None
    score: float = 0.0
    affiliate_url: Optional[str] = None


@dataclass
class GenericIdea:
    text: str
    item_index: int


class PostState(TypedDict):
    # Input
    post_id: int
    creator_id: int
    language: str
    tone: str
    photo_urls: List[str]
    voice_samples: List[str]

    # Context
    creator_profile: Dict[str, Any]

    # Analysis results
    outfit_items: List[Dict[str, Any]]
    occasion: str
    child_present: bool

    # Generated content
    caption: str
    outfit_description: str
    alt_text: str
    hashtags: List[str]

    # Product search
    search_queries: List[str]
    candidates: List[ProductCandidate]
    selected_products: List[ProductCandidate]
    generic_ideas: List[GenericIdea]

    # Script
    script_text: Optional[str]
    script_duration: Optional[int]
    script_word_count: Optional[int]

    # Control flow
    search_attempts: int
    current_version: int
    error: Optional[str]