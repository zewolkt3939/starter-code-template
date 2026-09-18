"""Node `human_review` — HITL interrupt cho hành động rủi ro (LangGraph 1.x).

Vì sao tồn tại: gap-analysis guidebook cũ có 0 nội dung về HITL. Pattern
chuẩn langgraph 1.x: node gọi `interrupt(payload)` → graph DỪNG, trả
`__interrupt__` cho client; client resume bằng `Command(resume=...)` —
node chạy lại từ đầu và `interrupt()` trả về giá trị resume. Yêu cầu
graph phải compile với checkpointer (đã có MemorySaver).
"""

from __future__ import annotations

import logging

from langgraph.types import interrupt

from src.agents.state import AgentState
from src.agents.tools import TOOL_REGISTRY

logger = logging.getLogger("ai20k.human_review")


async def human_review_node(state: AgentState) -> dict:
    """Chờ human phê duyệt pending_action; approve thì chạy tool tại đây."""
    pending = state.get("pending_action")
    if not pending:
        # Vào node này mà không có gì chờ duyệt là bug graph — raise, không im lặng.
        raise RuntimeError("human_review được gọi nhưng pending_action trống")

    answer = interrupt({
        "question": "Phê duyệt hành động rủi ro này của agent?",
        "tool": pending["tool"],
        "args": pending["args"],
    })

    if answer not in ("approve", "reject"):
        raise ValueError(f"Giá trị resume không hợp lệ: {answer!r} (chờ 'approve' | 'reject')")

    decisions = list(state.get("human_decisions", []))
    trace = list(state.get("tool_trace", []))

    if answer == "approve":
        try:
            output = TOOL_REGISTRY[pending["tool"]].invoke(pending["args"])
        except Exception as exc:  # giống act_node: lỗi tool là DỮ KIỆN, không làm sập graph
            logger.error("FAILED human_review — tool %s lỗi: %s", pending["tool"], exc)
            output = f"TOOL_ERROR: {exc}"
        trace.append({"tool": pending["tool"], "args": pending["args"], "output": str(output)})
        decisions.append({"tool": pending["tool"], "decision": "approve"})
        logger.info("human_review APPROVE — %s đã chạy", pending["tool"])
    else:
        output = "BLOCKED_BY_HUMAN"
        trace.append({"tool": pending["tool"], "args": pending["args"], "output": output})
        decisions.append({"tool": pending["tool"], "decision": "reject"})
        logger.warning("human_review REJECT — %s bị chặn", pending["tool"])

    return {
        "pending_action": None,
        "human_decisions": decisions,
        "tool_trace": trace,
        "stage": "assess",
    }
