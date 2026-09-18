"""Graph v2 — harness ReAct đúng: loop có hạn, router thật, HITL, checkpointer.

Vì sao tồn tại: graph v1 (đúng lỗi trong e1-current-docs) có 2 node format
chuỗi, should_continue() là no-op (error không bao giờ được set), tools
không bao giờ được gọi. Bản v2 sửa cả bốn lỗi harness:

  (a) ReAct loop có max_iterations (default 8) + node assess (self-
      assessment) + node finalize_with_partial (escape hatch — luôn có
      đường tới END, good practice #5 của team 011).
  (b) Conditional edges THẬT: 4 router, mỗi router trả giá trị khác nhau
      theo state (route_after_guardrail / route_after_reason /
      route_after_act / route_after_assess).
  (c) Checkpointer MemorySaver (langgraph 1.x import path) — bắt buộc để
      interrupt()/resume hoạt động.
  (d) HITL: tool rủi ro (RISKY_TOOL_NAMES, vd send_email) đi qua node
      human_review dùng interrupt() + Command(resume=...).

build_graph() nhận reason_fn / generate_fn injectable để test không cần
API key — mock LLM, không mock graph.
"""

from __future__ import annotations

import logging

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.types import Command

from src.agents.guardrails import GuardrailViolation, guardrails
from src.agents.nodes.act_node import act_node
from src.agents.nodes.assess_node import assess_node
from src.agents.nodes.finalize_node import GenerateFn, _make_finalize, llm_generate
from src.agents.nodes.human_review_node import human_review_node
from src.agents.nodes.reason_node import ReasonFn, llm_reason, make_reason_node
from src.agents.state import AgentState
from src.config import get_settings

logger = logging.getLogger("ai20k.graph")

__all__ = ["Command", "build_graph", "agent"]


async def guardrail_check_node(state: AgentState) -> dict:
    """Lớp guardrail 1 — chặn prompt injection TRƯỚC khi query chạm LLM."""
    try:
        guardrails.check_input(state.get("query", ""))
    except GuardrailViolation as exc:
        # Từ chối tường minh — KHÔNG phải silent fallback: state ghi rõ lý do.
        return {"refusal_reason": exc.detail, "stage": "refusal"}
    return {"stage": "guardrail"}


def make_entry_node(max_iterations: int):
    """Seed state loop-limit MỘT lần ở entry — router sau chỉ đọc state.

    Checkpointer giữ state theo thread_id, nên mỗi lượt chat mới phải reset các
    field per-turn — nếu không refusal/tool_trace/iteration_count của lượt trước
    dính sang lượt sau. Resume HITL đi qua Command, không qua entry, nên an toàn.
    """

    async def entry_node(state: AgentState) -> dict:
        return {
            "max_iterations": state.get("max_iterations", max_iterations),
            "iteration_count": 0,
            "refusal_reason": "",
            "tool_trace": [],
            "last_decision": {},
            "pending_action": None,
            "human_decisions": [],
            "response": "",
        }

    return entry_node


# ---------------------------------------------------------------------------
# Conditional edges THẬT — mỗi router trả về đích KHÁC NHAU theo state.
# (should_continue() cũ trả về 1 trong 2 giá trị mà nhánh error không bao
# giờ xảy ra — tức no-op. Bốn router dưới đây đều được test phủ.)
# ---------------------------------------------------------------------------

def route_after_guardrail(state: AgentState) -> str:
    """Input bị chặn -> finalize (nhắn từ chối); hợp lệ -> reason."""
    return "finalize" if state.get("refusal_reason") else "reason"


def route_after_reason(state: AgentState) -> str:
    """Quyết định vòng này: gọi tool -> act; đã đủ -> finalize."""
    decision = state.get("last_decision", {})
    return "act" if decision.get("action") == "tool" else "finalize"


def route_after_act(state: AgentState) -> str:
    """Tool rủi ro -> human_review (HITL); tool thường -> assess."""
    return "human_review" if state.get("pending_action") else "assess"


def route_after_assess(state: AgentState) -> str:
    """Self-assessment: đủ dữ kiện -> finalize; hết vòng -> partial; còn lại -> reason."""
    if state.get("last_decision", {}).get("enough_data", False):
        return "finalize"
    if state.get("iteration_count", 0) >= state.get("max_iterations", 8):
        logger.warning(
            "assess — hết %d vòng, escape hatch -> finalize_with_partial",
            state.get("max_iterations", 8),
        )
        return "finalize_with_partial"
    return "reason"


def build_graph(
    *,
    reason_fn: ReasonFn | None = None,
    generate_fn: GenerateFn | None = None,
    max_iterations: int | None = None,
    checkpointer=None,
) -> StateGraph:
    """Compile graph. Tham số injectable để test mock LLM, không gọi API thật."""
    settings = get_settings()
    max_iter = max_iterations if max_iterations is not None else settings.agent_max_iterations

    graph = StateGraph(AgentState)

    graph.add_node("entry", make_entry_node(max_iter))
    graph.add_node("guardrail_check", guardrail_check_node)
    graph.add_node("reason", make_reason_node(reason_fn or llm_reason))
    graph.add_node("act", act_node)
    graph.add_node("human_review", human_review_node)
    graph.add_node("assess", assess_node)
    graph.add_node("finalize", _make_finalize(generate_fn or llm_generate, partial=False))
    graph.add_node("finalize_with_partial", _make_finalize(generate_fn or llm_generate, partial=True))

    graph.set_entry_point("entry")
    graph.add_edge("entry", "guardrail_check")
    graph.add_conditional_edges("guardrail_check", route_after_guardrail, ["reason", "finalize"])
    graph.add_conditional_edges("reason", route_after_reason, ["act", "finalize"])
    graph.add_conditional_edges("act", route_after_act, ["human_review", "assess"])
    graph.add_edge("human_review", "assess")
    graph.add_conditional_edges(
        "assess",
        route_after_assess,
        ["reason", "finalize", "finalize_with_partial"],
    )
    graph.add_edge("finalize", END)
    graph.add_edge("finalize_with_partial", END)

    # (c) Checkpointer — MemorySaver (in-process). Prod đổi sang SqliteSaver/
    # PostgresSaver giữ nguyên phần còn lại (team 011 dùng SqliteSaver).
    return graph.compile(checkpointer=checkpointer if checkpointer is not None else MemorySaver())


agent = build_graph()
