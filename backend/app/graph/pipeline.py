from typing import Dict, Any, List
from langgraph.graph import StateGraph, END, START
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
import json
import httpx

from .state import PostState, ProductCandidate, GenericIdea
from ..core.config import settings


def get_llm(model: str = None):
    """Get Gemini LLM instance."""
    return ChatGoogleGenerativeAI(
        model=model or settings.GEMINI_MODEL_STRONG,
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.7,
        max_output_tokens=2048,
    )


def load_context(state: PostState) -> Dict[str, Any]:
    """Load creator profile and voice samples."""
    return {
        "creator_profile": state.get("creator_profile", {}),
        "voice_samples": state.get("voice_samples", []),
    }


def analyze_photo(state: PostState) -> Dict[str, Any]:
    """Analyze outfit photo using Gemini Vision."""
    llm = get_llm(settings.GEMINI_MODEL_STRONG)

    photo_urls = state["photo_urls"]
    language = state["language"]
    tone = state["tone"]

    system_prompt = f"""You are a fashion expert analyzing an outfit photo.
    Analyze the outfit and provide structured information.

    Language: {language}
    Tone: {tone}

    IMPORTANT RULES:
    1. Describe ONLY clothing items, colors, fabrics, and occasion.
    2. Do NOT describe any person's face, body, age, or physical features.
    3. If a child appears to be in the photo, set child_present to true but describe ONLY the clothing.
    4. Output valid JSON only."""

    user_prompt = """Analyze this outfit photo and return JSON with these fields:
    {
        "items": [
            {
                "name": "item name",
                "color": "color",
                "fabric": "fabric type",
                "category": "top/bottom/footwear/accessory"
            }
        ],
        "occasion": "occasion type",
        "child_present": false,
        "overall_style": "style description"
    }"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=[
            {"type": "text", "text": user_prompt},
            {"type": "image_url", "image_url": {"url": photo_urls[0]}}
        ])
    ]

    response = llm.invoke(messages)

    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        content = response.content
        start = content.find("{")
        end = content.rfind("}") + 1
        if start != -1 and end > start:
            result = json.loads(content[start:end])
        else:
            result = {
                "items": [],
                "occasion": "casual",
                "child_present": False,
                "overall_style": "fashionable outfit"
            }

    return {
        "outfit_items": result.get("items", []),
        "occasion": result.get("occasion", "casual"),
        "child_present": result.get("child_present", False),
    }


def write_caption(state: PostState) -> Dict[str, Any]:
    """Generate caption for the outfit."""
    llm = get_llm(settings.GEMINI_MODEL_STRONG)

    language = state["language"]
    tone = state["tone"]
    outfit_items = state["outfit_items"]
    occasion = state["occasion"]
    child_present = state["child_present"]
    voice_samples = state.get("voice_samples", [])

    voice_context = ""
    if voice_samples:
        voice_context = "\n\nHere are examples of the Creator's writing style:\n"
        for i, sample in enumerate(voice_samples[:5], 1):
            voice_context += f"{i}. {sample}\n"

    system_prompt = f"""You are a social media caption writer for fashion creators.
    Write engaging Instagram captions in {language} with a {tone} tone.

    RULES:
    1. Write in {language} only.
    2. Match the Creator's voice style from the examples provided.
    3. Do NOT mention any child if present - describe only clothing.
    4. Keep caption under 2200 characters (Instagram limit).
    5. Do NOT include hashtags in the caption (they are generated separately).
    6. Make it engaging and authentic.
    {voice_context}"""

    items_desc = ", ".join([f"{item['name']} ({item['color']})" for item in outfit_items])

    user_prompt = f"""Write a {tone} caption for this outfit:
    Items: {items_desc}
    Occasion: {occasion}

    Return JSON with:
    {{
        "caption": "the caption text",
        "version": 1
    }}"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    response = llm.invoke(messages)

    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        content = response.content
        start = content.find("{")
        end = content.rfind("}") + 1
        if start != -1 and end > start:
            result = json.loads(content[start:end])
        else:
            result = {"caption": response.content, "version": 1}

    return {
        "caption": result.get("caption", ""),
        "current_version": state.get("current_version", 0) + 1,
    }


def write_description(state: PostState) -> Dict[str, Any]:
    """Generate outfit description and alt text."""
    llm = get_llm(settings.GEMINI_MODEL_CHEAP)

    outfit_items = state["outfit_items"]
    language = state["language"]

    system_prompt = f"""You are a fashion description writer.
    Write clear, structured outfit descriptions in {language}.
    Also create accessible alt text for the outfit image."""

    items_desc = json.dumps(outfit_items, indent=2)

    user_prompt = f"""Based on these outfit items:
    {items_desc}

    Return JSON with:
    {{
        "description": "structured breakdown with items, colors, fabrics, occasion",
        "alt_text": "accessible description for screen readers"
    }}"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    response = llm.invoke(messages)

    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        content = response.content
        start = content.find("{")
        end = content.rfind("}") + 1
        if start != -1 and end > start:
            result = json.loads(content[start:end])
        else:
            result = {"description": "Outfit description", "alt_text": "Fashion outfit photo"}

    return {
        "outfit_description": result.get("description", ""),
        "alt_text": result.get("alt_text", ""),
    }


def generate_hashtags(state: PostState) -> Dict[str, Any]:
    """Generate hashtags for the post."""
    llm = get_llm(settings.GEMINI_MODEL_CHEAP)

    caption = state["caption"]
    outfit_items = state["outfit_items"]
    language = state["language"]
    occasion = state["occasion"]

    system_prompt = f"""You are a social media hashtag expert for fashion content.
    Generate relevant hashtags in {language} and English.
    Mix broad reach hashtags with niche fashion hashtags.
    Do NOT include brand, people, or location tags."""

    user_prompt = f"""Generate hashtags for this post:
    Caption: {caption[:200]}
    Items: {[item['name'] for item in outfit_items]}
    Occasion: {occasion}

    Return JSON with:
    {{
        "hashtags": ["tag1", "tag2", ...]
    }}

    Generate 15-25 hashtags."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    response = llm.invoke(messages)

    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        content = response.content
        start = content.find("{")
        end = content.rfind("}") + 1
        if start != -1 and end > start:
            result = json.loads(content[start:end])
        else:
            result = {"hashtags": ["fashion", "ootd", "style"]}

    return {"hashtags": result.get("hashtags", [])}


def plan_queries(state: PostState) -> Dict[str, Any]:
    """Plan search queries for product matching."""
    outfit_items = state["outfit_items"]
    language = state["language"]

    queries = []
    for item in outfit_items:
        name = item.get("name", "")
        color = item.get("color", "")
        query = f"{color} {name}".strip()
        queries.append(query)

    return {
        "search_queries": queries,
        "search_attempts": 0,
    }


def search_products(state: PostState) -> Dict[str, Any]:
    """Search for products using SerpAPI Google Shopping."""
    queries = state["search_queries"]
    candidates = []

    for query in queries:
        try:
            response = httpx.get(
                "https://serpapi.com/search",
                params={
                    "engine": "google_shopping",
                    "q": query,
                    "api_key": settings.SERPAPI_API_KEY,
                    "gl": "in",
                    "hl": state["language"],
                },
                timeout=10.0,
            )
            data = response.json()

            for item in data.get("shopping_results", [])[:5]:
                candidate = ProductCandidate(
                    source=item.get("source", ""),
                    title=item.get("title", ""),
                    price=item.get("price", ""),
                    image_url=item.get("thumbnail", ""),
                    merchant_url=item.get("link", ""),
                    google_url=item.get("product_link", ""),
                    score=0.0,
                )
                candidates.append(candidate)
        except Exception as e:
            print(f"Search error for '{query}': {e}")

    return {
        "candidates": candidates,
        "search_attempts": state.get("search_attempts", 0) + 1,
    }


def rank_candidates(state: PostState) -> Dict[str, Any]:
    """Rank product candidates using Gemini."""
    llm = get_llm(settings.GEMINI_MODEL_CHEAP)

    candidates = state["candidates"]
    outfit_items = state["outfit_items"]

    if not candidates:
        return {"selected_products": [], "generic_ideas": []}

    candidates_text = "\n".join([
        f"{i+1}. {c.title} - {c.price} from {c.source}"
        for i, c in enumerate(candidates[:20])
    ])

    items_desc = ", ".join([item["name"] for item in outfit_items])

    system_prompt = """You are a fashion product matcher.
    Rank products by how well they complement the outfit.
    Consider style, color coordination, and occasion fit."""

    user_prompt = f"""Outfit items: {items_desc}

    Available products:
    {candidates_text}

    Return JSON with:
    {{
        "selected_indices": [1, 2, 3],
        "generic_ideas": [
            {{"item_index": 0, "text": "styling idea description"}}
        ]
    }}

    Select up to 3 products that best complete the look.
    If no product is a good match for an item, include a generic_idea instead."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    response = llm.invoke(messages)

    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        content = response.content
        start = content.find("{")
        end = content.rfind("}") + 1
        if start != -1 and end > start:
            result = json.loads(content[start:end])
        else:
            result = {"selected_indices": [1, 2, 3], "generic_ideas": []}

    selected_indices = result.get("selected_indices", [])
    selected_products = []
    for idx in selected_indices:
        if 1 <= idx <= len(candidates):
            selected_products.append(candidates[idx - 1])

    generic_ideas = []
    for idea in result.get("generic_ideas", []):
        generic_ideas.append(GenericIdea(
            text=idea.get("text", ""),
            item_index=idea.get("item_index", 0),
        ))

    return {
        "selected_products": selected_products,
        "generic_ideas": generic_ideas,
    }


def check_search_results(state: PostState) -> str:
    """Conditional edge: decide next step based on search results."""
    selected = state.get("selected_products", [])
    attempts = state.get("search_attempts", 0)

    if len(selected) >= 2:
        return "resolve_links"
    elif attempts < 2:
        return "broaden_query"
    else:
        return "resolve_links"


def broaden_query(state: PostState) -> Dict[str, Any]:
    """Broaden search queries for better results."""
    queries = state["search_queries"]
    broadened = []
    for q in queries:
        parts = q.split()
        if len(parts) > 2:
            broadened.append(" ".join(parts[:2]))
        else:
            broadened.append(q)
    return {"search_queries": broadened}


def resolve_links(state: PostState) -> Dict[str, Any]:
    """Convert merchant URLs to affiliate links using Cuelinks."""
    selected_products = state["selected_products"]
    creator_id = state["creator_id"]

    for product in selected_products:
        if product.merchant_url:
            try:
                response = httpx.get(
                    "https://api.cuelinks.com/v2/convert_link",
                    params={
                        "url": product.merchant_url,
                        "subid": f"{settings.CUELINKS_SUBID}_{creator_id}",
                    },
                    headers={"Authorization": f"Bearer {settings.CUELINKS_API_KEY}"},
                    timeout=10.0,
                )
                data = response.json()
                product.affiliate_url = data.get("shortened_url", product.merchant_url)
            except Exception as e:
                print(f"Cuelinks error: {e}")
                product.affiliate_url = product.merchant_url

    return {"selected_products": selected_products}


def assemble_post(state: PostState) -> Dict[str, Any]:
    """Assemble final post data."""
    return {
        "caption": state.get("caption", ""),
        "outfit_description": state.get("outfit_description", ""),
        "alt_text": state.get("alt_text", ""),
        "hashtags": state.get("hashtags", []),
        "selected_products": state.get("selected_products", []),
        "generic_ideas": state.get("generic_ideas", []),
        "child_present": state.get("child_present", False),
    }


def write_script(state: PostState) -> Dict[str, Any]:
    """Generate voiceover script."""
    llm = get_llm(settings.GEMINI_MODEL_STRONG)

    duration = state.get("script_duration", 30)
    outfit_items = state.get("outfit_items", [])
    products = state.get("selected_products", [])
    language = state["language"]

    target_words = int(duration * 2.5)

    system_prompt = f"""You are a video scriptwriter for fashion creators.
    Write a {duration}-second voiceover script in {language}.

    Structure:
    1. Hook (first 3-5 seconds): attention-grabbing opener
    2. Outfit walkthrough: describe the outfit pieces
    3. Call to action: direct viewers to link

    Rules:
    - Target {target_words} words (+/- 10%)
    - Only mention products the Creator selected
    - Include optional disclosure line
    - Write in {language}"""

    items_desc = ", ".join([item["name"] for item in outfit_items])
    products_desc = ", ".join([p.title for p in products[:3]]) if products else "no products"

    user_prompt = f"""Duration: {duration} seconds
    Outfit items: {items_desc}
    Products: {products_desc}

    Return JSON with:
    {{
        "script": "the voiceover text",
        "disclosure": "optional disclosure line",
        "word_count": 75
    }}"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    response = llm.invoke(messages)

    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        content = response.content
        start = content.find("{")
        end = content.rfind("}") + 1
        if start != -1 and end > start:
            result = json.loads(content[start:end])
        else:
            result = {
                "script": response.content,
                "disclosure": "This post contains affiliate links.",
                "word_count": target_words,
            }

    return {
        "script_text": result.get("script", ""),
        "script_duration": duration,
        "script_word_count": result.get("word_count", target_words),
    }


def check_script_length(state: PostState) -> str:
    """Check if script word count is within range."""
    duration = state.get("script_duration", 30)
    word_count = state.get("script_word_count", 0)
    target = int(duration * 2.5)
    tolerance = target * 0.1

    if abs(word_count - target) <= tolerance:
        return "end"
    elif state.get("search_attempts", 0) < 2:
        return "rewrite"
    else:
        return "end"


def build_graph():
    """Build the LangGraph pipeline."""
    graph = StateGraph(PostState)

    # Add nodes
    graph.add_node("load_context", load_context)
    graph.add_node("analyze_photo", analyze_photo)
    graph.add_node("write_caption", write_caption)
    graph.add_node("write_description", write_description)
    graph.add_node("generate_hashtags", generate_hashtags)
    graph.add_node("plan_queries", plan_queries)
    graph.add_node("search_products", search_products)
    graph.add_node("rank_candidates", rank_candidates)
    graph.add_node("broaden_query", broaden_query)
    graph.add_node("resolve_links", resolve_links)
    graph.add_node("assemble_post", assemble_post)
    graph.add_node("write_script", write_script)

    # Add edges
    graph.add_edge(START, "load_context")
    graph.add_edge("load_context", "analyze_photo")
    graph.add_edge("analyze_photo", "write_caption")
    graph.add_edge("analyze_photo", "write_description")
    graph.add_edge("analyze_photo", "generate_hashtags")
    graph.add_edge("write_caption", "plan_queries")
    graph.add_edge("write_description", "plan_queries")
    graph.add_edge("generate_hashtags", "plan_queries")
    graph.add_edge("plan_queries", "search_products")
    graph.add_edge("search_products", "rank_candidates")

    # Conditional edge for search results
    graph.add_conditional_edges(
        "rank_candidates",
        check_search_results,
        {
            "resolve_links": "resolve_links",
            "broaden_query": "broaden_query",
        }
    )

    graph.add_edge("broaden_query", "search_products")
    graph.add_edge("resolve_links", "assemble_post")
    graph.add_edge("assemble_post", "write_script")

    graph.add_conditional_edges(
        "write_script",
        check_script_length,
        {
            "rewrite": "write_script",
            "end": END,
        }
    )

    return graph.compile()


def build_script_graph():
    """Build script-only graph (run after Creator selects products)."""
    graph = StateGraph(PostState)

    graph.add_node("write_script", write_script)

    graph.add_edge(START, "write_script")
    graph.add_conditional_edges(
        "write_script",
        check_script_length,
        {
            "rewrite": "write_script",
            "end": END,
        }
    )

    return graph.compile()