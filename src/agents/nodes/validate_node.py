"""Validate node — output schema validation + quality gate (C1 + C6).

Kiểm tra AgentAnswer có "safe" không (xem AgentAnswer.is_safe). Nếu fail →
quality_result FAILED → graph retry synthesize (conditional edge trong graph.py).
Chống loop vô tận bằng max_iterations.
"""

from __future__ import annotations

import logging

from src.agents.state import AgentState
from src.config import get_settings
from src.models.schemas import AgentAnswer

logger = logging.getLogger(__name__)


async def validate_node(state: AgentState) -> dict:
    """Validate AgentAnswer. Đánh dấu PASSED/FAILED."""
    answer_struct = state.get("answer_struct")
    iteration = state.get("iteration", 0)

    if not answer_struct:
        return {
            "quality_result": {
                "status": "FAILED",
                "reason": "missing_answer_struct",
            },
            "iteration": iteration,
        }

    try:
        answer = AgentAnswer(**answer_struct)
    except Exception as e:  # noqa: BLE001 — schema violation
        logger.warning("schema violation: %s", e)
        return {
            "quality_result": {"status": "FAILED", "reason": f"schema_error: {e}"},
            "iteration": iteration,
        }

    if not answer.is_safe():
        return {
            "quality_result": {
                "status": "FAILED",
                "reason": "unsafe_answer (citation missing or low-confidence supported)",
            },
            "iteration": iteration,
        }

    return {
        "quality_result": {"status": "PASSED", "reason": "ok"},
        "iteration": iteration,
    }


def should_retry(state: AgentState) -> str:
    """Conditional edge: PASSED hoặc hết iteration → 'end'; ngược lại 'retry'.

    Inspire team 003 (should_retry pattern). max_iterations từ settings.
    """
    max_iter = get_settings().agent_max_iterations
    qr = state.get("quality_result", {}) or {}
    iteration = state.get("iteration", 0)
    if qr.get("status") == "PASSED" or iteration >= max_iter:
        return "end"
    return "retry"
