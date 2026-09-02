from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"] = "user"
    content: str

class RouteDecision(BaseModel):
    selected_model: str
    routing_mode: Literal["auto", "manual"] = "auto"
    intent_category: Literal["general", "advisor", "heavy_logic", "fast", "fallback"] = "general"
    reason: str
    confidence: float = 1.0
    tier_used: Literal["tier1_regex", "tier2_classifier", "manual_override", "fallback"] = "tier1_regex"

class RouteRequest(BaseModel):
    message: str
    manual_model: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    messages: Optional[List[ChatMessage]] = None
    model: Optional[str] = None  # None for auto-routing, or model name for manual override
    temperature: Optional[float] = 0.7
    system_prompt: Optional[str] = None
    stream: bool = True

class ChatResponse(BaseModel):
    response: str
    route_info: RouteDecision
    model: str
    done: bool = True

class ModelDetails(BaseModel):
    name: str
    size_bytes: int = 0
    size_formatted: str = ""
    modified_at: Optional[str] = None
    category: str = "general"
    badge_color: str = "green"  # green (default), yellow (advisor), purple (deep logic), blue (fallback)
    is_available: bool = True
