"""Retrieve node — RAG mock + citation contract (C1 + C2, inspire team 006).

Mock-first: nếu chưa có vector store (chroma/etc.), dùng knowledge base in-memory
để template chạy được ngay. Khi team setup Chroma, chỉ cần thay body hàm
`_retrieve_chunks` — interface (context + citations) giữ nguyên.
"""

from __future__ import annotations

from src.agents.state import AgentState

# Knowledge base mock. Thay bằng Chroma/Pinecone khi sẵn sàng.
_MOCK_KB: dict[str, str] = {
    "chunk_demo_1": "AI20K Build Phase kéo dài 6 tuần. Mỗi đội build 1 AI Agent.",
    "chunk_demo_2": "LangGraph dùng StateGraph để orchestrate các node.",
    "chunk_demo_3": "Demo Day là ngày nộp bài cuối kỳ, chấm bởi BTC.",
}


async def retrieve_node(state: AgentState) -> dict:
    """Lấy context từ knowledge base + gán citation ids."""
    query = state.get("query", "")
    chunks = _retrieve_chunks(query)
    context = "\n\n".join(f"[cite:{cid}] {text}" for cid, text in chunks.items())
    return {
        "context": context,
        "citations": [f"cite:{cid}" for cid in chunks],
    }


def _retrieve_chunks(query: str) -> dict[str, str]:
    """Mock retrieval. Khi có vector store, thay bằng similarity search.

    Mock: trả tất cả chunk (đủ để demo citation). Production: top-k similarity.
    """
    # TODO(team): thay bằng Chroma similarity search khi setup.
    return dict(_MOCK_KB)
