"""Node `finalize` / `finalize_with_partial` — sinh câu trả lời cuối qua schema.

Vì sao tồn tại: output cuối là thứ user nhìn thấy — PHẢI qua lớp guardrail
(viền FinalAnswer + check_output_text chống leak system prompt / API key).
Node partial là escape hatch: trả lời với dữ kiện có được + cảnh báo rõ
ràng là thiếu, thay vì treo hay bịa.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from src.agents.guardrails import guardrails
from src.agents.state import AgentState
from src.models.schemas import FinalAnswer
from src.services.llm import get_llm

logger = logging.getLogger("ai20k.finalize")

GenerateFn = Callable[..., Awaitable[FinalAnswer]]

_GENERATE_PROMPT = """<role>Bạn viết câu trả lời cuối cho user.</role>
<context>
Query: {query}
Tool trace:
{tool_trace}
{partial_note}
</context>
<instructions>
Chỉ dùng dữ kiện trong tool trace. Thiếu thì nói thiếu. confidence theo mức chắc chắn thực tế.
</instructions>
<output_format>Đúng schema FinalAnswer (answer, confidence, used_tools).</output_format>"""


async def llm_generate(state: AgentState, partial: bool = False) -> FinalAnswer:
    """Default generate_fn — model mạnh (generate tier) vì đây là đầu ra chính."""
    llm = get_llm("generate").with_structured_output(FinalAnswer)
    trace = "\n".join(f"- {t['tool']}({t['args']}) -> {t['output']}" for t in state.get("tool_trace", []))
    partial_note = (
        "\nLƯU Ý: hết vòng lặp tối đa mà chưa đủ dữ kiện — trả lời phần có được và ghi rõ phần thiếu."
        if partial else ""
    )
    prompt = _GENERATE_PROMPT.format(
        query=state.get("query", ""),
        tool_trace=trace or "(không có tool nào được gọi)",
        partial_note=partial_note,
    )
    return await llm.ainvoke(prompt)


def _make_finalize(generate_fn: GenerateFn | None, partial: bool):
    fn = generate_fn or llm_generate

    async def finalize_node(state: AgentState) -> dict:
        # Nhánh từ chối do guardrail input — không gọi LLM, trả lời canned tường minh.
        if state.get("refusal_reason"):
            refusal = FinalAnswer(
                answer=(
                    "Tôi không thể xử lý yêu cầu này: "
                    f"{state['refusal_reason']}"
                ),
                confidence=1.0,
                used_tools=[],
            )
            return {"response": refusal.answer, "stage": "refusal"}

        raw = await fn(state, partial=partial)
        final = guardrails.validate_output(raw, FinalAnswer, source="finalize")
        guardrails.check_output_text(final.answer)  # leak system prompt/key -> raise

        if partial:
            warning = (
                "\n\n[Trả lời một phần] Agent đã hết số vòng tối đa "
                f"({state.get('max_iterations', 8)}) mà chưa đủ dữ kiện — "
                "câu trả lời dựa trên dữ kiện thu thập được đến thời điểm này."
            )
            answer = final.answer + warning
        else:
            answer = final.answer

        logger.info("finalize (partial=%s) confidence=%.2f", partial, final.confidence)
        return {"response": answer, "stage": "partial" if partial else "finalize"}

    return finalize_node
