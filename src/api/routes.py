"""API routes v2 — truyền thread_id cho checkpointer để HITL resume hoạt động.

Vì sao đổi: graph v2 compile với MemorySaver — invoke bắt buộc có
`config={"configurable": {"thread_id": ...}}`. Client giữ session_id,
gửi lại kèm Command(resume=...) khi user duyệt/từ chối hành động rủi ro.
"""

import logging

from fastapi import APIRouter, HTTPException
from langgraph.types import Command
from pydantic import BaseModel

from src.agents.graph import agent
from src.models.schemas import ChatRequest, ChatResponse

logger = logging.getLogger("ai20k.api")

router = APIRouter()


def _config(session_id: str) -> dict:
    return {"configurable": {"thread_id": session_id}}


def _to_chat_response(result: dict, session_id: str) -> ChatResponse:
    # Cả /chat lẫn /chat/resume đều có thể dừng ở interrupt (vd agent muốn gửi email thứ 2)
    if "__interrupt__" in result:
        interrupts = result["__interrupt__"]
        payload = getattr(interrupts[0], "value", interrupts[0])
        return ChatResponse(
            response=f"[CẦN PHÊ DUYỆT] {payload}. POST /chat/resume với resume='approve' hoặc 'reject'.",
            analysis="HITL interrupt",
            session_id=session_id,
        )
    trace = result.get("tool_trace", [])
    analysis = "; ".join(f"{t['tool']}({t['args']}) -> {str(t['output'])[:60]}" for t in trace)
    return ChatResponse(response=result.get("response", ""), analysis=analysis, session_id=session_id)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Chat với AI agent. Nếu agent đang chờ human review, response chứa hướng dẫn resume."""
    try:
        result = await agent.ainvoke({"query": request.message}, config=_config(request.session_id))
        return _to_chat_response(result, request.session_id)
    except Exception as exc:
        logger.error("FAILED /chat — %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


class ResumeRequest(BaseModel):
    session_id: str  # bắt buộc — lấy từ ChatResponse.session_id của /chat
    resume: str  # "approve" | "reject"


@router.post("/chat/resume", response_model=ChatResponse)
async def chat_resume(request: ResumeRequest) -> ChatResponse:
    """Resume sau HITL interrupt — phê duyệt hoặc từ chối hành động rủi ro."""
    try:
        result = await agent.ainvoke(Command(resume=request.resume), config=_config(request.session_id))
        return _to_chat_response(result, request.session_id)
    except Exception as exc:
        logger.error("FAILED /chat/resume — %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/status")
async def agent_status():
    """Kiểm tra trạng thái agent."""
    return {"status": "ready", "agent": "LangGraph Agent v2.0"}
