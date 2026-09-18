"""Test HITL interrupt — tên test đọc như spec (pattern team 008 Buddy).

Risky tool send_email PHẢI dừng graph chờ human; approve mới chạy,
reject thì tool bị chặn và graph vẫn kết thúc có kiểm soát.
"""

import pytest
from langgraph.types import Command

from src.models.schemas import AgentDecision
from tests.conftest import ScriptedReasoner, make_test_graph

CONFIG = {"configurable": {"thread_id": "hitl-thread"}}


def _email_decision() -> AgentDecision:
    return AgentDecision(
        thought="gửi email xác nhận",
        action="tool",
        tool_name="send_email",
        tool_args={"to": "hocvien@example.com", "subject": "Xác nhận", "body": "OK"},
    )


def _final() -> AgentDecision:
    return AgentDecision(thought="đủ rồi", action="final", enough_data=True, final_answer="xong")


@pytest.mark.asyncio
async def test_risky_tool_interrupts_and_runs_only_after_approval():
    reasoner = ScriptedReasoner([_email_decision(), _final()])
    graph = make_test_graph(reasoner)

    result = await graph.ainvoke({"query": "Gửi email xác nhận cho học viên"}, config=CONFIG)
    assert "__interrupt__" in result, "send_email phải dừng graph chờ human review"

    resumed = await graph.ainvoke(Command(resume="approve"), config=CONFIG)
    assert resumed["human_decisions"] == [{"tool": "send_email", "decision": "approve"}]
    assert "Email sent to 'hocvien@example.com'" in resumed["tool_trace"][-1]["output"]
    assert "FAKE ANSWER" in resumed["response"]


@pytest.mark.asyncio
async def test_rejected_risky_tool_is_blocked_and_graph_still_terminates():
    reasoner = ScriptedReasoner([_email_decision(), _final()])
    graph = make_test_graph(reasoner)

    await graph.ainvoke({"query": "Gửi email gì đó"}, config=CONFIG)
    resumed = await graph.ainvoke(Command(resume="reject"), config=CONFIG)

    assert resumed["human_decisions"][0]["decision"] == "reject"
    assert resumed["tool_trace"][-1]["output"] == "BLOCKED_BY_HUMAN"
    assert "Email sent" not in resumed["tool_trace"][-1]["output"]
    assert "FAKE ANSWER" in resumed["response"]


@pytest.mark.asyncio
async def test_safe_tool_never_interrupts():
    reasoner = ScriptedReasoner([
        AgentDecision(thought="calc", action="tool", tool_name="calculate", tool_args={"expression": "1+1"}),
        _final(),
    ])
    graph = make_test_graph(reasoner)
    result = await graph.ainvoke({"query": "Tính 1+1"}, config=CONFIG)
    assert "__interrupt__" not in result
    assert result["tool_trace"][0]["output"] == "2"


class _BrokenTool:
    def invoke(self, args):
        raise RuntimeError("SMTP từ chối người nhận")


@pytest.mark.asyncio
async def test_approved_risky_tool_error_is_recorded_not_raised(monkeypatch):
    from src.agents.nodes import human_review_node

    monkeypatch.setitem(human_review_node.TOOL_REGISTRY, "send_email", _BrokenTool())
    reasoner = ScriptedReasoner([_email_decision(), _final()])
    graph = make_test_graph(reasoner)
    config = {"configurable": {"thread_id": "hitl-broken-tool"}}

    await graph.ainvoke({"query": "Gửi email"}, config=config)
    resumed = await graph.ainvoke(Command(resume="approve"), config=config)

    assert resumed["tool_trace"][-1]["output"].startswith("TOOL_ERROR:")
    assert "FAKE ANSWER" in resumed["response"]
