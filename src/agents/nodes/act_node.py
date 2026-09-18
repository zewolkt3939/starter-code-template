"""Node `act` — thực thi tool an toàn; tool rủi ro thì HOÃN sang human_review.

Vì sao tồn tại: cần một chỗ duy nhất trung gian giữa "LLM muốn gọi tool"
và "tool thực sự chạy" để (a) kiểm tra tool có rủi ro không (HITL route),
(b) ghi tool_trace làm minh chứng eval, (c) lỗi tool được ghi TƯỜNG MINH
vào trace cho vòng reason sau xử lý — không nuốt lỗi âm thầm.
"""

from __future__ import annotations

import logging

from src.agents.state import AgentState
from src.agents.tools import RISKY_TOOL_NAMES, TOOL_REGISTRY

logger = logging.getLogger("ai20k.act")


async def act_node(state: AgentState) -> dict:
    decision = state.get("last_decision", {})
    tool_name = decision.get("tool_name", "")
    tool_args: dict = decision.get("tool_args", {}) or {}
    trace = list(state.get("tool_trace", []))

    if tool_name in RISKY_TOOL_NAMES:
        # KHÔNG chạy — đẩy sang human_review chờ interrupt()/phê duyệt.
        logger.warning("act — tool rủi ro %s hoãn sang human_review", tool_name)
        return {"pending_action": {"tool": tool_name, "args": tool_args}, "stage": "human_review"}

    if tool_name not in TOOL_REGISTRY:
        # reason_node đã chặn, đây là defense-in-depth (belts and braces).
        logger.error("FAILED act — tool ngoài registry: %r", tool_name)
        raise ValueError(f"Tool ngoài registry: {tool_name!r}")

    tool = TOOL_REGISTRY[tool_name]
    try:
        output = tool.invoke(tool_args)
    except Exception as exc:  # lỗi tool là DỮ KIỆN cho vòng reason sau
        logger.error("FAILED act — tool %s lỗi: %s", tool_name, exc)
        output = f"TOOL_ERROR: {exc}"
    trace.append({"tool": tool_name, "args": tool_args, "output": str(output)})
    logger.info("act — %s(%s) -> %s", tool_name, tool_args, str(output)[:80])
    return {"tool_trace": trace, "pending_action": None, "stage": "act"}
