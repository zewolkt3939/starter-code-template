"""AgentState v2 — supervisor state theo good practice #1 (team 002 DevCoach).

Vì sao tồn tại: state cũ chỉ có query/analysis/response — không có chỗ nào
track vòng lặp ReAct, không biết đang ở stage nào, không có escape hatch.
Bản v2 thêm: iteration_count (chống loop vô hạn), stage Literal (một chỗ
duy nhất merge state), pending_action (HITL interrupt), tool_trace (minh
chứng cho eval + report).
"""

from __future__ import annotations

from typing import Literal, TypedDict

Stage = Literal[
    "guardrail",   # kiểm tra input đầu vào
    "reason",      # LLM quyết định: gọi tool hay trả lời
    "act",         # thực thi tool an toàn
    "human_review",  # HITL interrupt cho tool rủi ro (send_email, delete...)
    "assess",      # self-assessment: đủ dữ kiện chưa? vượt max_iterations?
    "finalize",    # sinh câu trả lời cuối đầy đủ
    "partial",     # sinh câu trả lời với dữ kiện thiếu (escape hatch)
    "refusal",     # từ chối do guardrail chặn input
]


class AgentState(TypedDict, total=False):
    """State schema cho LangGraph agent — mọi node đọc/ghi vào đây.

    total=False cho phép fields optional; node nào cũng có thể đọc bằng
    state.get(...) an toàn.
    """

    # Input
    query: str

    # Vòng lặp ReAct
    iteration_count: int
    max_iterations: int
    stage: Stage

    # Kết quả reason (AgentDecision đã qua guardrail)
    last_decision: dict  # AgentDecision.model_dump()

    # Tool execution trace — minh chứng để eval + debug
    tool_trace: list[dict]  # [{"tool": ..., "args": ..., "output": ...}]

    # HITL: tool rủi ro chờ human phê duyệt
    pending_action: dict | None  # {"tool": ..., "args": ...}
    human_decisions: list[dict]  # [{"tool":..., "decision": "approve"|"reject"}]

    # Output
    response: str
    refusal_reason: str
    error: str
    metadata: dict
