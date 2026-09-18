"""Tool registry — MỘT chỗ duy nhất liệt kê tool agent được dùng.

Vì sao tồn tại: reason node cần biết tool hợp lệ để validate quyết định
của LLM (LLM bịa tên tool → fail loudly thay vì KeyError ở xa chỗ lỗi).
Tool rủi ro đánh dấu qua RISKY_TOOL_NAMES để graph route HITL.
"""

from src.agents.tools.knowledge import calculate, search_knowledge
from src.agents.tools.mcp_tool import mcp_knowledge_lookup
from src.agents.tools.risky_tools import RISKY_TOOL_NAMES, send_email

TOOL_REGISTRY: dict = {
    "search_knowledge": search_knowledge,
    "calculate": calculate,
    "mcp_knowledge_lookup": mcp_knowledge_lookup,
    "send_email": send_email,
}

__all__ = [
    "TOOL_REGISTRY",
    "RISKY_TOOL_NAMES",
    "search_knowledge",
    "calculate",
    "mcp_knowledge_lookup",
    "send_email",
]
