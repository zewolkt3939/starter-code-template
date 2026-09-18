"""Tool kiểu MCP (Model Context Protocol) — minh họa tích hợp MCP server.

Vì sao tồn tại: MCP là hướng chính 2026 để agent gọi tool từ server bên
ngoài (filesystem, browser, DB...) mà không phải viết client riêng cho
từng nguồn. Template này chưa cài MCP server thật — thay vào đó tool dưới
đây GIỮ NGUYÊN HÌNH DẠNG giao thức MCP (JSON-RPC 2.0, method
"tools/call") nhưng thực thi local. Khi đội cài MCP server thật, chỉ cần
thay thân hàm `_mcp_call` bằng HTTP/stdio client tới server — phần còn
lại của agent (tool registry, HITL, guardrails) không đổi.

Spec: https://modelcontextprotocol.io/specification (JSON-RPC 2.0,
method "tools/list" / "tools/call", kết quả wrap trong content[]).
"""

import json
import uuid

from langchain_core.tools import tool

# Địa chỉ mô phỏng của "MCP server" — thực tế là hàm local bên dưới.
_MCP_SERVER_URL = "mcp://localhost/knowledge-lookup"


def _mcp_call(method: str, params: dict) -> dict:
    """Gửi một JSON-RPC 2.0 request theo đúng wire format của MCP.

    Thực tế: `httpx.post(MCP_SERVER_HTTP_URL, json=request)`.
    Ở đây trả kết quả canned để template chạy được không cần server.
    """
    request = {
        "jsonrpc": "2.0",
        "id": uuid.uuid4().hex[:8],
        "method": method,  # vd "tools/call"
        "params": params,
    }
    # ---- FAKE TRANSPORT (đội thay bằng HTTP call thật) ----
    fake_result = {
        "content": [
            {
                "type": "text",
                "text": (
                    f"[MCP demo] Đã gọi {method!r} trên server "
                    f"{_MCP_SERVER_URL} với params={json.dumps(params, ensure_ascii=False)}. "
                    "Đội thay transport này bằng MCP client thật."
                ),
            }
        ],
        "isError": False,
    }
    return {"jsonrpc": "2.0", "id": request["id"], "result": fake_result}


@tool
def mcp_knowledge_lookup(topic: str) -> str:
    """Tra cứu kiến thức qua MCP server bên ngoài (demo protocol shape).

    Giữ đơn giản: 1 tool, 1 method. Khi cài MCP thật, đội có thể dùng
    langchain-mcp-adapters để auto-convert "tools/list" thành nhiều
    @tool — xem spec: https://modelcontextprotocol.io

    Args:
        topic: Chủ đề cần tra cứu.

    Returns:
        Text content đầu tiên trong result — đúng cách MCP trả tool result.
    """
    response = _mcp_call(
        "tools/call",
        {"name": "knowledge_lookup", "arguments": {"topic": topic}},
    )
    result = response["result"]
    if result.get("isError"):
        raise RuntimeError(f"MCP tool call lỗi: {result}")
    return result["content"][0]["text"]
