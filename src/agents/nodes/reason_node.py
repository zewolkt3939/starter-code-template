"""Node `reason` — LLM quyết định vòng này gọi tool hay đã trả lời được.

Vì sao tồn tại: template cũ có analyze_node chỉ format chuỗi — tools
KHÔNG BAO GIỜ được gọi (đúng lỗi e1-current-docs). Node này là bước
reasoning thực của vòng ReAct: đầu ra là AgentDecision đã qua guardrail
schema-first; tên tool bịa sẽ bị chặn tại đây, không phải ở runtime xa.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from src.agents.guardrails import guardrails
from src.agents.state import AgentState
from src.agents.tools import TOOL_REGISTRY
from src.models.schemas import AgentDecision
from src.services.llm import get_llm

logger = logging.getLogger("ai20k.reason")

ReasonFn = Callable[[AgentState], Awaitable[AgentDecision]]

_REASON_PROMPT = """<role>Bạn là reasoning step của một AI agent kiểu ReAct.</role>
<context>
Query của user: {query}
Kết quả các tool đã chạy (mới nhất cuối):
{tool_trace}
Đã dùng {iteration}/{max_iterations} vòng.
Tool khả dụng: {tool_names}
</context>
<instructions>
Quyết định MỘT trong hai:
1. action="tool" — cần thêm dữ kiện: chọn 1 tool + args.
2. action="final" — đủ dữ kiện: đưa final_answer.
Đặt enough_data=true khi đã có đủ để trả lời.
KHÔNG bịa tên tool ngoài danh sách. KHÔNG bịa dữ kiện không có trong tool trace.
</instructions>
<output_format>Đúng schema AgentDecision.</output_format>
<verification>Tự đọc lại: tool_name có trong danh sách? final_answer không bịa?</verification>"""


async def llm_reason(state: AgentState) -> AgentDecision:
    """Default reason_fn — dùng model rẻ (classify tier) vì việc này là routing."""
    llm = get_llm("classify").with_structured_output(AgentDecision)
    trace = "\n".join(f"- {t['tool']}({t['args']}) -> {t['output']}" for t in state.get("tool_trace", []))
    prompt = _REASON_PROMPT.format(
        query=state.get("query", ""),
        tool_trace=trace or "(chưa có)",
        iteration=state.get("iteration_count", 0),
        max_iterations=state.get("max_iterations", 8),
        tool_names=", ".join(TOOL_REGISTRY),
    )
    return await llm.ainvoke(prompt)


def make_reason_node(reason_fn: ReasonFn | None = None):
    """Factory — cho test inject reason_fn giả định (không gọi API thật)."""
    fn = reason_fn or llm_reason

    async def reason_node(state: AgentState) -> dict:
        raw_decision = await fn(state)
        # Lớp guardrail 2: output của reason BẮT BUỘC qua schema — sai là
        # raise tại đây (fail loudly), không sửa khéo cho qua.
        decision = guardrails.validate_output(raw_decision, AgentDecision, source="reason")
        if decision.action == "tool" and decision.tool_name not in TOOL_REGISTRY:
            logger.error("FAILED reason — tool bịa %r ngoài registry", decision.tool_name)
            raise ValueError(
                f"AgentDecision chọn tool không tồn tại: {decision.tool_name!r}. "
                f"Tool hợp lệ: {sorted(TOOL_REGISTRY)}"
            )
        logger.info("reason iter=%d action=%s tool=%s", state.get("iteration_count", 0), decision.action, decision.tool_name)
        return {"last_decision": decision.model_dump(), "stage": "reason"}

    return reason_node
