import re
import json
import logging
from typing import AsyncGenerator, Optional, Tuple
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatRequest, ChatResponse, RouteDecision
from app.services.router_service import router_service
from app.services.ollama_service import ollama_service
from app.services.rag_service import rag_service
from app.services.memory_worker import memory_worker
from app.modules.finance import finance_module
from app.modules.health import health_module
from app.db.database import AsyncSessionLocal
from app.db.repository import DatabaseRepository

logger = logging.getLogger("ogcai.chat_router")
router = APIRouter(prefix="/api/chat", tags=["chat"])


async def execute_precision_tool_if_matched(user_message: str) -> Tuple[str, str]:
    """
    Detect if the user message requests a precision calculation or daily module tool
    (Compound Interest, Monthly Finance Summary, Daily Routine) and execute it deterministically.
    Returns (markdown_prefix_for_user, system_prompt_context_for_llm).
    """
    text = user_message.strip()

    # 1. Compound Interest & Portfolio Growth Simulation
    if any(kw in text for kw in ["ดอกเบี้ยทบต้น", "จำลองการเติบโตของเงินทุน", "คำนวณดอกเบี้ย"]) or (
        "เงินต้น" in text and ("ผลตอบแทน" in text or "%" in text)
    ):
        principal = 100000.0
        monthly = 0.0
        rate = 5.0
        years = 5

        p_match = re.search(r"เงินต้น\s*([\d,]+(?:\.\d+)?)", text)
        if not p_match:
            p_match = re.search(r"เงินฝาก\s*([\d,]+(?:\.\d+)?)", text)
        if p_match:
            principal = float(p_match.group(1).replace(",", ""))

        m_match = re.search(r"(?:ออมเพิ่ม|ฝากเพิ่ม|เดือนละ)\s*([\d,]+(?:\.\d+)?)", text)
        if m_match:
            monthly = float(m_match.group(1).replace(",", ""))

        r_match = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
        if r_match:
            rate = float(r_match.group(1))

        y_match = re.search(r"(\d+)\s*ปี", text)
        if y_match:
            years = max(1, min(50, int(y_match.group(1))))

        calc = finance_module.calculate_compound_growth(
            principal=principal,
            monthly_contribution=monthly,
            annual_rate_pct=rate,
            years=years
        )
        chart_url = calc.get("chart", {}).get("image_url", "")

        yearly_lines = []
        yb = calc["yearly_breakdown"]
        for y, dep, bal in zip(yb["years"], yb["total_deposits"], yb["total_balances"]):
            if y == 0:
                continue
            profit = bal - dep
            yearly_lines.append(f"- **ปีที่ {y}:** เงินต้นสะสม `{dep:,.0f} ฿` ➔ มูลค่ารวม **`{bal:,.2f} ฿`** *(ดอกเบี้ยสะสม `+{profit:,.2f} ฿`)*")

        md_block = (
            f"### 📊 ผลการคำนวณแม่นยำ (OGCAI Precision Sandbox)\n"
            f"- 💰 **เงินต้นเริ่มต้น:** `{principal:,.2f} บาท`\n"
            f"- 💵 **ออมเพิ่มต่อเดือน:** `{monthly:,.2f} บาท/เดือน`\n"
            f"- 📈 **ผลตอบแทนเฉลี่ย:** `{rate}% ต่อปี` (ทบต้นรายเดือน เป็นเวลา `{years} ปี`)\n"
            f"- 🏆 **มูลค่าพอร์ตสุทธิปลายปีที่ {years}:** **`{calc['final_balance']:,.2f} บาท`**\n"
            f"- ✨ **เงินต้นสะสมรวม:** `{calc['total_deposits']:,.2f} บาท` | **ดอกเบี้ยทบต้นที่ได้รับ:** **`+{calc['total_interest_earned']:,.2f} บาท`**\n\n"
            f"**สรุปการเติบโตแยกรายปี:**\n" + "\n".join(yearly_lines) + "\n\n"
        )
        if chart_url:
            md_block += f"![กราฟการเติบโตของเงินทุน ({years} ปี)]({chart_url})\n\n---\n💡 **บทวิเคราะห์และคำแนะนำเพิ่มเติม:**\n"

        llm_context = (
            f"[ผลลัพธ์จากเครื่องคำนวณ Precision Sandbox ที่แสดงให้ผู้ใช้เห็นแล้ว]\n"
            f"เงินต้น {principal:,.2f} บาท, ออมเดือนละ {monthly:,.2f} บาท, ผลตอบแทน {rate}% ต่อปี, ระยะเวลา {years} ปี:\n"
            f"- เงินต้นสะสมรวม = {calc['total_deposits']:,.2f} บาท\n"
            f"- ดอกเบี้ยทบต้นรวม = {calc['total_interest_earned']:,.2f} บาท\n"
            f"- มูลค่าพอร์ตสุดท้าย = {calc['final_balance']:,.2f} บาท\n"
            f"คำสั่ง: ตัวเลขตารางและกราฟถูกแสดงให้ผู้ใช้เห็นด้านบนเรียบร้อยแล้ว ให้คุณสรุปข้อคิดเห็นสั้นๆ 2-3 ข้อเกี่ยวกับพลังของดอกเบี้ยทบต้นหรือคำแนะนำการจัดพอร์ตที่เหมาะสมกับผลตอบแทน {rate}% ต่อปี โดยใช้ตัวเลขชุดนี้เท่านั้น ห้ามคำนวณใหม่เอง"
        )
        return md_block, llm_context

    # 2. Monthly Finance Summary
    if any(kw in text for kw in ["สรุปรายรับ-จ่าย", "สรุปสถานะการเงิน", "รายรับ รายจ่าย"]):
        try:
            async with AsyncSessionLocal() as session:
                summary = await finance_module.get_monthly_summary(session=session)
            chart_url = (summary.get("chart") or {}).get("image_url", "")
            md_block = (
                f"### 💰 สรุปสถานะการเงินประจำเดือน ({summary['month']})\n"
                f"- 🟢 **รายรับรวม:** `+{summary['total_income']:,.2f} บาท`\n"
                f"- 🔴 **รายจ่ายรวม:** `-{summary['total_expense']:,.2f} บาท`\n"
                f"- 💎 **เงินออมสุทธิ:** `{summary['net_balance']:,.2f} บาท` *(อัตราการออม `{summary['savings_rate_pct']}%`)*\n\n"
            )
            if chart_url:
                md_block += f"![สัดส่วนค่าใช้จ่ายประจำเดือน]({chart_url})\n\n---\n"
            llm_context = (
                f"[ข้อมูลการเงินจริงจากฐานข้อมูลเดือน {summary['month']}]\n"
                f"รายรับรวม: {summary['total_income']:,.2f} บาท, รายจ่ายรวม: {summary['total_expense']:,.2f} บาท, "
                f"คงเหลือสุทธิ: {summary['net_balance']:,.2f} บาท, อัตราการออม: {summary['savings_rate_pct']}%\n"
                f"คำสั่ง: ให้คำแนะนำสั้นๆ ในการบริหารจัดการเงินจากตัวเลขข้างต้น"
            )
            return md_block, llm_context
        except Exception as e:
            logger.warning(f"Precision finance summary skipped: {e}")

    return "", ""


async def build_augmented_system_prompt(
    user_message: str,
    custom_system_prompt: Optional[str] = None,
    precision_context: str = ""
) -> str:
    """
    Combine base persona, long-term user profile facts, relevant RAG context from Vault, and Precision Tool data.
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

    # 4. Precision Tool Computed Context
    if precision_context:
        sections.append(precision_context)

    return "\n\n".join(sections)


async def sse_event_generator(request: ChatRequest) -> AsyncGenerator[str, None]:
    """
    Generator yielding Server-Sent Events (SSE) for real-time streaming chat with Memory,
    RAG integration, Precision Sandbox Tools, and automatic VRAM Model Fallback.
    """
    try:
        # 1. Determine Model via Dynamic Router
        decision: RouteDecision = await router_service.route_message(
            message=request.message,
            manual_model=request.model
        )
        active_model = decision.selected_model
        
        # 2. Send metadata header event
        metadata_payload = {
            "type": "metadata",
            "model": active_model,
            "selected_model": active_model,
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

        # 4. Execute Precision Tool if applicable (e.g. Compound Interest / Finance Summary)
        precision_md, precision_context = await execute_precision_tool_if_matched(request.message)
        accumulated_content = []

        if precision_md:
            accumulated_content.append(precision_md)
            yield f"event: token\ndata: {json.dumps({'type': 'token', 'content': precision_md, 'model': active_model}, ensure_ascii=False)}\n\n"

        # 5. Build Augmented System Prompt (Profile + Vault RAG + Precision Data)
        system_prompt = await build_augmented_system_prompt(
            request.message,
            request.system_prompt,
            precision_context=precision_context
        )
        
        # 6. Format message history (Short-Term Context)
        messages = []
        if request.messages:
            for m in request.messages:
                messages.append({"role": m.role, "content": m.content})
        elif request.conversation_id:
            try:
                async with AsyncSessionLocal() as session:
                    db_messages = await DatabaseRepository.get_messages(
                        session=session,
                        conversation_id=request.conversation_id,
                        limit=10
                    )
                    for m in db_messages:
                        messages.append({"role": m.role, "content": m.content})
            except Exception as e:
                logger.warning(f"Failed to fetch conversation history for {request.conversation_id}: {e}")

        # Ensure the current user message is included
        if not messages or messages[-1].get("content") != request.message:
            messages.append({"role": "user", "content": request.message})
            
        # 7. Stream Tokens from Ollama (with Automatic VRAM Fallback)
        stream_completed = False
        last_chunk = {}

        async for chunk in ollama_service.stream_chat(
            messages=messages,
            model=active_model,
            system_prompt=system_prompt,
            temperature=request.temperature or 0.7
        ):
            last_chunk = chunk

            # Handle automatic model fallback notification
            if chunk.get("type") == "model_fallback":
                active_model = chunk.get("fallback_model", active_model)
                fallback_meta = {
                    "type": "metadata",
                    "model": active_model,
                    "selected_model": active_model,
                    "routing_mode": decision.routing_mode,
                    "intent_category": decision.intent_category,
                    "reason": chunk.get("reason", decision.reason),
                    "tier_used": "vram_auto_fallback",
                    "confidence": decision.confidence
                }
                yield f"event: metadata\ndata: {json.dumps(fallback_meta, ensure_ascii=False)}\n\n"
                continue

            if "error" in chunk:
                # If we already streamed deterministic precision tool output, finish gracefully instead of failing!
                if accumulated_content:
                    stream_completed = True
                    break
                yield f"event: error\ndata: {json.dumps({'error': chunk['error']}, ensure_ascii=False)}\n\n"
                return
                
            token = chunk.get("content", "")
            done = chunk.get("done", False)
            
            if token:
                accumulated_content.append(token)
                token_payload = {
                    "type": "token",
                    "content": token,
                    "model": active_model
                }
                yield f"event: token\ndata: {json.dumps(token_payload, ensure_ascii=False)}\n\n"
                
            if done:
                stream_completed = True
                break

        if stream_completed or accumulated_content:
            assistant_reply = "".join(accumulated_content)
            assistant_msg_id = None
            
            # 8. Save Assistant Message to SQLite
            if request.conversation_id and assistant_reply:
                try:
                    async with AsyncSessionLocal() as session:
                        saved_msg = await DatabaseRepository.add_message(
                            session=session,
                            conversation_id=request.conversation_id,
                            role="assistant",
                            content=assistant_reply,
                            model=active_model,
                            intent_category=decision.intent_category
                        )
                        await session.commit()
                        assistant_msg_id = saved_msg.id
                except Exception as e:
                    logger.error(f"Error saving assistant message: {e}")

            # 9. Trigger Background Memory Extractor
            memory_worker.trigger_background_extraction(request.message, assistant_reply)

            done_payload = {
                "type": "done",
                "model": active_model,
                "message_id": assistant_msg_id,
                "done": True,
                "total_duration": last_chunk.get("total_duration"),
                "eval_count": last_chunk.get("eval_count")
            }
            yield f"event: done\ndata: {json.dumps(done_payload, ensure_ascii=False)}\n\n"
                
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
    Non-streaming fallback chat endpoint with Memory, Precision Tool & RAG context injection.
    """
    decision = await router_service.route_message(
        message=request.message,
        manual_model=request.model
    )
    active_model = decision.selected_model

    precision_md, precision_context = await execute_precision_tool_if_matched(request.message)
    system_prompt = await build_augmented_system_prompt(
        request.message,
        request.system_prompt,
        precision_context=precision_context
    )

    messages = []
    if request.messages:
        for m in request.messages:
            messages.append({"role": m.role, "content": m.content})
    else:
        messages.append({"role": "user", "content": request.message})
        
    full_reply = []
    if precision_md:
        full_reply.append(precision_md)

    async for chunk in ollama_service.stream_chat(
        messages=messages,
        model=active_model,
        system_prompt=system_prompt,
        temperature=request.temperature or 0.7
    ):
        if chunk.get("type") == "model_fallback":
            active_model = chunk.get("fallback_model", active_model)
            continue
        if "error" in chunk:
            if full_reply:
                break
            raise HTTPException(status_code=500, detail=chunk["error"])
        token = chunk.get("content", "")
        if token:
            full_reply.append(token)
            
    reply_text = "".join(full_reply)
    
    # Save conversation & trigger memory worker
    if request.conversation_id:
        async with AsyncSessionLocal() as session:
            await DatabaseRepository.add_message(session, request.conversation_id, "user", request.message, intent_category=decision.intent_category)
            await DatabaseRepository.add_message(session, request.conversation_id, "assistant", reply_text, model=active_model, intent_category=decision.intent_category)
            await session.commit()

    memory_worker.trigger_background_extraction(request.message, reply_text)

    return ChatResponse(
        response=reply_text,
        route_info=decision,
        model=active_model,
        done=True
    )
