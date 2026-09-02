from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db, backup_database
from app.db.repository import DatabaseRepository

router = APIRouter(prefix="/api", tags=["memory"])

# Pydantic Request/Response Models
class CreateConversationRequest(BaseModel):
    title: Optional[str] = "การสนทนาใหม่"

class UpdateConversationRequest(BaseModel):
    title: str

class ProfileFactRequest(BaseModel):
    key: str
    value: str
    category: Optional[str] = "general"
    confidence: Optional[float] = 1.0

class StarredKnowledgeRequest(BaseModel):
    title: str
    content: str
    summary: Optional[str] = ""
    tags: Optional[str] = ""
    message_id: Optional[str] = None

# ----------------- Conversations -----------------
@router.get("/conversations")
async def list_conversations(limit: int = 50, db: AsyncSession = Depends(get_db)):
    convs = await DatabaseRepository.list_conversations(db, limit=limit)
    return [
        {
            "id": c.id,
            "title": c.title,
            "is_pinned": c.is_pinned,
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat()
        }
        for c in convs
    ]

@router.post("/conversations")
async def create_conversation(req: CreateConversationRequest, db: AsyncSession = Depends(get_db)):
    conv = await DatabaseRepository.create_conversation(db, title=req.title or "การสนทนาใหม่")
    return {
        "id": conv.id,
        "title": conv.title,
        "is_pinned": conv.is_pinned,
        "created_at": conv.created_at.isoformat() if conv.created_at else "",
        "updated_at": conv.updated_at.isoformat() if conv.updated_at else ""
    }

@router.get("/conversations/{conv_id}")
async def get_conversation(conv_id: str, db: AsyncSession = Depends(get_db)):
    conv = await DatabaseRepository.get_conversation(db, conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {
        "id": conv.id,
        "title": conv.title,
        "is_pinned": conv.is_pinned,
        "created_at": conv.created_at.isoformat(),
        "updated_at": conv.updated_at.isoformat(),
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "model": m.model,
                "intent_category": m.intent_category,
                "is_starred": m.is_starred,
                "timestamp": m.timestamp.isoformat()
            }
            for m in conv.messages
        ]
    }

@router.patch("/conversations/{conv_id}")
async def update_conversation_title(conv_id: str, req: UpdateConversationRequest, db: AsyncSession = Depends(get_db)):
    success = await DatabaseRepository.update_conversation_title(db, conv_id, req.title)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"success": True, "title": req.title}

@router.delete("/conversations/{conv_id}")
async def delete_conversation(conv_id: str, db: AsyncSession = Depends(get_db)):
    success = await DatabaseRepository.delete_conversation(db, conv_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"success": True}

# ----------------- Star Message -----------------
@router.post("/messages/{message_id}/star")
async def toggle_star_message(message_id: str, db: AsyncSession = Depends(get_db)):
    msg = await DatabaseRepository.toggle_star_message(db, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"id": msg.id, "is_starred": msg.is_starred}

# ----------------- User Profile Memory -----------------
@router.get("/profile")
async def get_profile(db: AsyncSession = Depends(get_db)):
    facts = await DatabaseRepository.get_all_profile_facts(db)
    return [
        {
            "id": f.id,
            "key": f.key,
            "value": f.value,
            "category": f.category,
            "confidence": f.confidence,
            "updated_at": f.updated_at.isoformat()
        }
        for f in facts
    ]

@router.post("/profile")
async def set_profile_fact(req: ProfileFactRequest, db: AsyncSession = Depends(get_db)):
    fact = await DatabaseRepository.set_profile_fact(
        db,
        key=req.key,
        value=req.value,
        category=req.category or "general",
        confidence=req.confidence or 1.0
    )
    return {
        "id": fact.id,
        "key": fact.key,
        "value": fact.value,
        "category": fact.category,
        "confidence": fact.confidence
    }

@router.delete("/profile/{fact_id}")
async def delete_profile_fact(fact_id: int, db: AsyncSession = Depends(get_db)):
    success = await DatabaseRepository.delete_profile_fact(db, fact_id)
    if not success:
        raise HTTPException(status_code=404, detail="Fact not found")
    return {"success": True}

# ----------------- Starred Knowledge -----------------
@router.get("/starred")
async def list_starred_knowledge(limit: int = 50, db: AsyncSession = Depends(get_db)):
    items = await DatabaseRepository.list_starred_knowledge(db, limit=limit)
    return [
        {
            "id": item.id,
            "message_id": item.message_id,
            "title": item.title,
            "summary": item.summary,
            "tags": item.tags,
            "content": item.content,
            "created_at": item.created_at.isoformat()
        }
        for item in items
    ]

@router.post("/starred")
async def create_starred_knowledge(req: StarredKnowledgeRequest, db: AsyncSession = Depends(get_db)):
    item = await DatabaseRepository.create_starred_knowledge(
        db,
        title=req.title,
        content=req.content,
        summary=req.summary or "",
        tags=req.tags or "",
        message_id=req.message_id
    )
    return {"id": item.id, "title": item.title, "created_at": item.created_at.isoformat()}

@router.delete("/starred/{item_id}")
async def delete_starred_knowledge(item_id: str, db: AsyncSession = Depends(get_db)):
    success = await DatabaseRepository.delete_starred_knowledge(db, item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"success": True}

# ----------------- Database Backup -----------------
@router.post("/database/backup")
async def trigger_backup():
    path = backup_database()
    if not path:
        raise HTTPException(status_code=500, detail="Backup failed")
    return {"status": "success", "backup_file": path}
