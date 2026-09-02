import json
import logging
from typing import AsyncGenerator, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatRequest, ChatResponse, RouteDecision
from app.services.router_service import router_service
from app.services.ollama_service import ollama_service
from app.services.rag_service import rag_service
from app.services.memory_worker import memory_worker
from app.db.database import AsyncSessionLocal
from app.db.repository import DatabaseRepository

logger = logging.getLogger("ogcai.chat_router")
router = APIRouter(prefix="/api/chat", tags=["chat"])

async def build_augmented_system_prompt(
    user_message: str,
    custom_system_prompt: Optional[str] = None
) -> str:
    """
    Combine base persona, long-term user profile facts, and relevant RAG context from Vault.
    """
    sections = []
    
    # 1. Base Assistant Persona
    base_persona = (
        "คุณคือ OGCAI (Personal Local AI Assistant) ผู้ช่วยอัจฉริยะส่วนตัวที่ทำงานบนเครื่องของผู้ใช้ 100% "
        "ให้คำตอบที่กระชับ สุภาพ แม่นยำ และเป็นประโยชน์สูงสุดเสมอ ใช้ภาษาไทยเป็นหลักเว้นแต่ผู้ใช้จะถามเป็นภาษาอื่น"
    )
    if custom_system_prompt:
        sections.append(custom_system_prompt)
    else:
        sections.append(base_persona)

    # 2. Long-term Profile Facts
    async with AsyncSessionLocal() as session:
        profile_context = await DatabaseRepository.get_profile_context_string(session)
        if profile_context:
            sections.append(profile_context)

    # 3. Vault RAG Context
    rag_context = rag_service.build_rag_context(user_message, top_k=2)
    if rag_context:
        sections.append(rag_context)

    return "\n\n".join(sections)


async def sse_event_generator(request: ChatRequest) -> AsyncGenerator[str, None]:
    """
    Generator yielding Server-Sent Events (SSE) for real-time streaming chat with Memory & RAG integration.
    """
    try:
        # 1. Determine Model via Dynamic Router
        decision: RouteDecision = await router_service.route_message(
            message=request.message,
            manual_model=request.model
        )
        
        # 2. Send metadata header event
        metadata_payload = {
            "type": "metadata",
            "model": decision.selected_model,
            "selected_model": decision.selected_model,
            "routing_mode": decision.routing_mode,
            "intent_category": decision.intent_category,
            "reason": decision.reason,
            "tier_used": decision.tier_used,
            "confidence": decision.confidence
        }
        yield f"event: metadata\ndata: {json.dumps(metadata_payload, ensure_ascii=False)}\n\n"

        # 3. Save User Message to SQLite if conversation_id provided
        if request.conversation_id:
            try:
                async with AsyncSessionLocal() as session:
                    await DatabaseRepository.add_message(
                        session=session,
                        conversation_id=request.conversation_id,
                        role="user",
                        content=request.message,
                        intent_category=decision.intent_category
                    )
                    await session.commit()
            except Exception as e:
                logger.error(f"Error saving user message to database: {e}")

        # 4. Build Augmented System Prompt (Profile + Vault RAG)
        system_prompt = await build_augmented_system_prompt(request.message, request.system_prompt)
        
        # 5. Format message history
        messages = []
        if request.messages:
            for m in request.messages:
                messages.append({"role": m.role, "content": m.content})
        else:
            messages.append({"role": "user", "content": request.message})
            
        # 6. Stream Tokens from Ollama
        accumulated_content = []
        async for chunk in ollama_service.stream_chat(
            messages=messages,
            model=decision.selected_model,
            system_prompt=system_prompt,
            temperature=request.temperature or 0.7
        ):
            if "error" in chunk:
                yield f"event: error\ndata: {json.dumps({'error': chunk['error']}, ensure_ascii=False)}\n\n"
                return
                
            token = chunk.get("content", "")
            done = chunk.get("done", False)
            
            if token:
                accumulated_content.append(token)
                token_payload = {
                    "type": "token",
                    "content": token,
                    "model": decision.selected_model
                }
                yield f"event: token\ndata: {json.dumps(token_payload, ensure_ascii=False)}\n\n"
                
            if done:
                assistant_reply = "".join(accumulated_content)
                
                # 7. Save Assistant Message to SQLite
                if request.conversation_id and assistant_reply:
                    try:
                        async with AsyncSessionLocal() as session:
                            await DatabaseRepository.add_message(
                                session=session,
                                conversation_id=request.conversation_id,
                                role="assistant",
                                content=assistant_reply,
                                model=decision.selected_model,
                                intent_category=decision.intent_category
                            )
                            await session.commit()
                    except Exception as e:
                        logger.error(f"Error saving assistant message: {e}")

                # 8. Trigger Background Memory Extractor
                memory_worker.trigger_background_extraction(request.message, assistant_reply)

                done_payload = {
                    "type": "done",
                    "model": decision.selected_model,
                    "done": True,
                    "total_duration": chunk.get("total_duration"),
                    "eval_count": chunk.get("eval_count")
                }
                yield f"event: done\ndata: {json.dumps(done_payload, ensure_ascii=False)}\n\n"
                break
                
    except Exception as e:
        logger.error(f"Error in SSE generator: {e}")
        err_payload = {"type": "error", "error": str(e)}
        yield f"event: error\ndata: {json.dumps(err_payload, ensure_ascii=False)}\n\n"


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream chat response using Server-Sent Events (SSE) with dynamic model routing,
    user memory recall, and Knowledge Vault RAG augmentation.
    """
    return StreamingResponse(
        sse_event_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("", response_model=ChatResponse)
async def chat_non_stream(request: ChatRequest):
    """
    Non-streaming fallback chat endpoint with Memory & RAG context injection.
    """
    decision = await router_service.route_message(
        message=request.message,
        manual_model=request.model
    )
    
    # Build System Prompt
    system_prompt = await build_augmented_system_prompt(request.message, request.system_prompt)

    messages = []
    if request.messages:
        for m in request.messages:
            messages.append({"role": m.role, "content": m.content})
    else:
        messages.append({"role": "user", "content": request.message})
        
    full_reply = []
    async for chunk in ollama_service.stream_chat(
        messages=messages,
        model=decision.selected_model,
        system_prompt=system_prompt,
        temperature=request.temperature or 0.7
    ):
        if "error" in chunk:
            raise HTTPException(status_code=500, detail=chunk["error"])
        token = chunk.get("content", "")
        if token:
            full_reply.append(token)
            
    reply_text = "".join(full_reply)
    
    # Save conversation & trigger memory worker
    if request.conversation_id:
        async with AsyncSessionLocal() as session:
            await DatabaseRepository.add_message(session, request.conversation_id, "user", request.message, intent_category=decision.intent_category)
            await DatabaseRepository.add_message(session, request.conversation_id, "assistant", reply_text, model=decision.selected_model, intent_category=decision.intent_category)
            await session.commit()

    memory_worker.trigger_background_extraction(request.message, reply_text)

    return ChatResponse(
        response=reply_text,
        route_info=decision,
        model=decision.selected_model,
        done=True
    )
