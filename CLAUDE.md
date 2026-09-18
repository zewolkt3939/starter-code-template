# CLAUDE.md — Project context cho Claude Code (C4/C5)

> Inspire team 001 (PROJECT_CONTEXT Quick Rehydrate) + team 008 (CLAUDE.md structure).

## Quick Rehydrate (≤ 60s)

Đọc nhanh khi mất context:
- **Đây là**: AI20K Agent Template — starter code cho học viên VinUni build AI Agent.
- **Stack**: Python 3.12, FastAPI, LangGraph 1.x, LangChain 1.x, Pydantic v2.
- **Mock-first**: agent chạy được KHÔNG cần OPENAI_API_KEY (xem `src/services/llm.py`).
- **Chạy server**: `uvicorn src.main:app --reload` → http://localhost:8000/docs
- **Chạy test**: `pytest tests/ -v`
- **Chạy eval**: `python eval/run_eval.py`

## Current Invariants (để không drift)

- **Source of truth kỹ thuật**: code trong `src/`. File `.md` (kể cả file này) chỉ là
  tóm tắt — khi mâu thuẫn, CODE WINS (inspire team 011 source-of-truth rule).
- **Agent graph**: `src/agents/graph.py` — ReAct harness loop: guardrail → reason → act
  (tools, HITL interrupt cho risky tools) → assess → finalize (escape hatch max-iterations).
  Pattern pipeline thay thế: safety → retrieve → synthesize → validate (nodes/ còn lại,
  dùng khi cần RAG pipeline tuyến tính thay vì ReAct loop). Đừng thêm node mà không cập nhật state schema.
- **Prompts**: nằm ở `prompts/*.md` (external file, `{{placeholder}}`). KHÔNG nhúng
  prompt dài trong Python string.
- **Safety guardrail**: DANGER_KEYWORDS ở `nodes/safety_node.py`. Domain-specific →
  team phải cập nhật theo app của mình.
- **Logging hooks**: `.claude/.cursor/.codex/.gemini/.github` auto-log prompt vào
  `.ai-log/`. KHÔNG disable, KHÔNG bypass `--no-verify`.

## Commands hay dùng

```bash
make test          # pytest
make lint          # ruff check
make run           # uvicorn
python eval/run_eval.py
```

Slash commands (Claude Code): `/feature`, `/eval` (xem `.claude/commands/`).

## Kiến trúc

```
src/agents/
  graph.py            # LangGraph orchestration (retry loop, safety gate)
  state.py            # AgentState TypedDict
  prompts.py          # loader + SHARED_RULES
  personas.py         # persona registry (frozen dataclass)
  nodes/              # reason, act, assess, human_review, finalize (ReAct loop)
  #                     # + safety, retrieve, synthesize, validate (pattern pipeline)
  tools/knowledge.py  # @tool: search_knowledge (RAG+citation), calculate (safe eval)
prompts/              # system_prompt.md, safeguards.md, citation_rules.md
eval/                 # golden_dataset + runner + LLM-judge + cost + thresholds
```

## Quyết định kỹ thuật (ADR ngắn)

- **Mock-first LLM**: để template chạy được ngay khi clone → giảm friction sinh viên.
- **External prompt files**: tách prompt khỏi code → mentor review được, diff rõ.
- **Defence-in-depth safety**: guardrail ở cả prompt (safeguards.md) LẪN code
  (safety_node) → chống jailbreak bỏ qua 1 lớp.
- **Retry loop trong graph**: dùng conditional edge thay vì try/except đệ quy.
