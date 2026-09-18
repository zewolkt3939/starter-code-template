"""Shared fixtures — mock LLM qua injection, KHÔNG gọi API thật.

Vì sao tồn tại: graph v2 nhận reason_fn/generate_fn injectable nên test
không cần monkeypatch ChatOpenAI — mock đúng tầng (tại seam), phần graph
được test thật 100%.
"""

from unittest.mock import AsyncMock

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from langgraph.checkpoint.memory import MemorySaver

from src.agents.graph import build_graph
from src.models.schemas import AgentDecision, FinalAnswer


class ScriptedReasoner:
    """Reason giả định — phát lần lượt các decision cho sẵn, đếm số lần gọi."""

    def __init__(self, decisions: list[AgentDecision]):
        self.decisions = list(decisions)
        self.calls = 0

    async def __call__(self, state) -> AgentDecision:
        self.calls += 1
        if not self.decisions:
            raise AssertionError("ScriptedReasoner hết decision — graph loop nhiều hơn dự kiến")
        return self.decisions.pop(0)


class AlwaysToolReasoner:
    """Luôn đòi gọi tool — dùng test escape hatch max_iterations."""

    def __init__(self):
        self.calls = 0

    async def __call__(self, state) -> AgentDecision:
        self.calls += 1
        return AgentDecision(
            thought=f"vòng {self.calls}: vẫn cần thêm dữ kiện",
            action="tool",
            tool_name="search_knowledge",
            tool_args={"query": state.get("query", "")},
            enough_data=False,
        )


async def fake_generate(state, partial: bool = False) -> FinalAnswer:
    """Generate giả định — gói tool trace + human decisions vào câu trả lời."""
    trace = state.get("tool_trace", [])
    outputs = "; ".join(f"{t['tool']}={t['output']}" for t in trace) or "no-tools"
    humans = "; ".join(f"human:{h['decision']}" for h in state.get("human_decisions", [])) or "human:none"
    return FinalAnswer(
        answer=f"FAKE ANSWER for {state.get('query', '')!r}. tools: {outputs}. {humans}.",
        confidence=0.9,
        used_tools=[t["tool"] for t in trace],
    )


@pytest_asyncio.fixture
async def client():
    """Async HTTP client for testing API endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
def mock_llm():
    """Mock LLM to avoid calling OpenAI during tests."""
    mock = AsyncMock()
    mock.ainvoke.return_value = AsyncMock(content="Mocked LLM response")
    return mock


def make_test_graph(reasoner, max_iterations: int = 8, checkpointer=None):
    """Build graph với LLM giả — helper dùng chung các test agent."""
    return build_graph(
        reason_fn=reasoner,
        generate_fn=fake_generate,
        max_iterations=max_iterations,
        checkpointer=checkpointer if checkpointer is not None else MemorySaver(),
    )


# Import cuối file để tránh circular import khi conftest được load sớm.
from src.main import app  # noqa: E402
