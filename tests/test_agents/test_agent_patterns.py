"""Tests cho agent patterns mới (C1/C6) — safety short-circuit, prompt loader,
schema validation, retry routing.

Giúp regression safety khi đổi prompt/model (inspire team 008 eval-thinking).
"""

import pytest

from src.agents.nodes.safety_node import safety_node
from src.agents.nodes.validate_node import should_retry
from src.agents.personas import PERSONAS, get_persona
from src.agents.prompts import SHARED_RULES, build_system_prompt, load_prompt
from src.config import get_settings
from src.models.schemas import AgentAnswer


@pytest.mark.asyncio
async def test_safety_node_short_circuits_danger():
    """Defence-in-depth: danger keyword → bypass LLM."""
    result = await safety_node({"query": "tôi muốn tự hại"})
    assert result["safety_flag"] == "danger"
    assert result["bypass"] is True
    assert "cảnh báo" in result["response"].lower() or "an toàn" in result["response"].lower()


@pytest.mark.asyncio
async def test_safety_node_passes_safe_query():
    result = await safety_node({"query": "AI20K kéo dài bao lâu?"})
    assert result["safety_flag"] == "ok"
    assert result["bypass"] is False


def test_prompt_loader_renders_placeholders():
    """External prompt file pattern: placeholder substitution works."""
    prompt = build_system_prompt()
    assert "{{shared_rules}}" not in prompt, "placeholder chưa được substitute"
    assert "{{safeguards}}" not in prompt
    assert "<role>" in prompt
    assert "<verification>" in prompt
    assert SHARED_RULES.split("\n")[0] in prompt


def test_prompt_loader_caches():
    """@lru_cache: gọi 2 lần trả cùng object (inspire team 003)."""
    a = load_prompt("system_prompt.md")
    b = load_prompt("system_prompt.md")
    assert a is b


def test_agent_answer_schema_lock():
    """Pydantic schema-lock: confidence ngoài [0,1] → validation error."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        AgentAnswer(verdict="supported", confidence=1.5, answer="x", citation_ids=["c1"])
    with pytest.raises(ValidationError):
        AgentAnswer(verdict="bogus", confidence=0.5, answer="x", citation_ids=[])


def test_agent_answer_is_safe_conservative_bias():
    """Conservative bias (team 012): claim mà không cite = unsafe."""
    unsafe = AgentAnswer(verdict="supported", confidence=0.9, answer="x", citation_ids=[])
    assert unsafe.is_safe() is False
    safe = AgentAnswer(verdict="uncertain", confidence=0.3, answer="x", citation_ids=[])
    assert safe.is_safe() is True


def test_should_retry_routes_on_quality():
    """Conditional retry edge (team 003)."""
    passed = {"quality_result": {"status": "PASSED"}, "iteration": 0}
    assert should_retry(passed) == "end"
    failed_fresh = {"quality_result": {"status": "FAILED"}, "iteration": 0}
    assert should_retry(failed_fresh) == "retry"
    max_iter = {"quality_result": {"status": "FAILED"}, "iteration": get_settings().agent_max_iterations}
    assert should_retry(max_iter) == "end"


def test_personas_registry_is_frozen():
    """Persona registry (team 002): frozen dataclass, immutable."""
    p = get_persona("mentor")
    assert p.temperature == 0.5
    # fallback
    assert get_persona("nonexistent").name == "default"
    assert "default" in PERSONAS
