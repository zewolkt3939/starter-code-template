"""Tools cho agent (C1). Hai tool mẫu:

- `calculate`: arithmetic an toàn (AST, KHÔNG dùng eval) — giữ từ template cũ.
- `search_knowledge`: tool RAG trả kết quả + citation (inspire team 006 citation
  contract). Mock-first; thay body khi có vector store.

Pattern LangChain `@tool` → agent có thể gọi qua tool-calling (ReAct).
"""

from __future__ import annotations

import ast
import operator

from langchain_core.tools import tool

# Safe operator mapping (KHÔNG dùng eval — defense against injection).
_SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


@tool
def search_knowledge(query: str) -> str:
    """Tìm kiếm trong knowledge base. Trả kết quả kèm citation [cite:chunk_id].

    Args:
        query: Câu hỏi cần tìm.

    Returns:
        Đoạn kiến thức + citation id.
    """
    # TODO(team): thay bằng Chroma similarity search khi setup.
    return "[cite:chunk_demo_1] Kết quả mock cho: " + query


@tool
def calculate(expression: str) -> str:
    """Tính biểu thức toán an toàn (không eval). Hỗ trợ + - * / // % ** và ngoặc.

    Args:
        expression: Biểu thức, vd "2 + 3 * 4".

    Returns:
        Kết quả.
    """
    try:
        tree = ast.parse(expression, mode="eval")
        return str(_eval_node(tree.body))
    except (SyntaxError, ValueError, TypeError, ZeroDivisionError) as e:
        return f"Lỗi tính toán: {e}"


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant: {type(node.value)}")
    if isinstance(node, ast.UnaryOp):
        op = _SAFE_OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError(f"Unsupported op: {type(node.op).__name__}")
        return op(_eval_node(node.operand))
    if isinstance(node, ast.BinOp):
        op = _SAFE_OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError(f"Unsupported op: {type(node.op).__name__}")
        return op(_eval_node(node.left), _eval_node(node.right))
    raise ValueError(f"Unsupported expression: {type(node).__name__}")


TOOLS = [search_knowledge, calculate]
