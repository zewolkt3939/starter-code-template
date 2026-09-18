"""Test tool registry + MCP-style tool — chạy được không cần MCP server thật."""



from src.agents.tools import RISKY_TOOL_NAMES, TOOL_REGISTRY
from src.agents.tools.mcp_tool import _mcp_call, mcp_knowledge_lookup


def test_registry_lists_every_tool():
    assert set(TOOL_REGISTRY) == {
        "search_knowledge",
        "calculate",
        "mcp_knowledge_lookup",
        "send_email",
    }


def test_every_risky_tool_exists_in_registry():
    assert RISKY_TOOL_NAMES <= set(TOOL_REGISTRY)


def test_mcp_wire_format_follows_jsonrpc_spec():
    """Tool MCP phải giữ hình dạng JSON-RPC 2.0 + content[] của spec MCP."""
    response = _mcp_call("tools/call", {"name": "knowledge_lookup", "arguments": {"topic": "mcp"}})
    assert response["jsonrpc"] == "2.0"
    assert "id" in response
    result = response["result"]
    assert result["isError"] is False
    assert result["content"][0]["type"] == "text"
    assert "topic" in result["content"][0]["text"] or "mcp" in result["content"][0]["text"]


def test_mcp_tool_invocable_as_langchain_tool():
    output = mcp_knowledge_lookup.invoke({"topic": "checkpointing"})
    assert "MCP demo" in output


def test_calculate_rejects_arbitrary_code():
    out = TOOL_REGISTRY["calculate"].invoke({"expression": "__import__('os').system('ls')"})
    assert out.startswith("Lỗi tính toán")
