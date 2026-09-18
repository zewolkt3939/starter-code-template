"""Synthesize node — gọi LLM, parse ra AgentAnswer (C1, inspire team 009/012).

Pattern: ưu tiên `with_structured_output` (ép schema ở layer LLM). Nếu provider
không hỗ trợ (vd mock, một số model) → fallback: gọi thường + parse JSON thủ công
+ validate bằng Pydantic. Graceful degradation, KHÔNG silent fail.
"""

from __future__ import annotations

import json
import logging

from src.agents.prompts import build_system_prompt
from src.agents.state import AgentState
from src.models.schemas import AgentAnswer
from src.services.llm import get_llm

logger = logging.getLogger(__name__)


async def synthesize_node(state: AgentState) -> dict:
    """Gọi LLM, parse ra AgentAnswer, ghi vào state."""
    iteration = state.get("iteration", 0)
    query = state.get("query", "")
    context = state.get("context", "")
    system_prompt = build_system_prompt()

    user_msg = (
        f"Question: {query}\n\n"
        f"Context:\n{context}\n\n"
        f"Trả JSON đúng schema AgentAnswer (verdict, confidence, answer, citation_ids)."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_msg},
    ]

    try:
        llm = get_llm()
        answer = await _get_structured_answer(llm, messages)
    except Exception as e:  # noqa: BLE001 — log + fallback, không silent (anti-pattern team 002)
        logger.exception("synthesize_node LLM failed (iteration %s)", iteration)
        return {
            "quality_result": {"status": "FAILED", "reason": f"llm_error: {e}"},
            "iteration": iteration + 1,
            "error": str(e),
        }

    return {
        "answer_struct": answer.model_dump(),
        "response": _render_answer(answer),
        "analysis": f"verdict={answer.verdict} confidence={answer.confidence}",
        "iteration": iteration,
    }


async def _get_structured_answer(llm, messages) -> AgentAnswer:
    """Thử with_structured_output; fallback parse JSON thủ công."""
    try:
        structured = llm.with_structured_output(AgentAnswer)
        return await structured.ainvoke(messages)
    except NotImplementedError:
        # Provider không hỗ trợ structured output (vd mock, model cũ).
        logger.info("with_structured_output unsupported — fallback JSON parse.")
        res = await llm.ainvoke(messages)
        content = getattr(res, "content", str(res))
        return _parse_answer(content)


def _parse_answer(content: str) -> AgentAnswer:
    """Parse JSON từ content LLM, validate bằng AgentAnswer schema."""
    text = content.strip()
    # Bỏ wrapping ```json ...``` nếu có
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM output không phải JSON hợp lệ: {e}; got: {text[:200]}")
    return AgentAnswer(**data)


def _render_answer(answer: AgentAnswer) -> str:
    """Render answer thành chuỗi user-facing + citation inline."""
    cites = " ".join(f"[cite:{cid}]" for cid in answer.citation_ids)
    return f"{answer.answer} {cites}".strip()
