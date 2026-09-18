---
title: "Context Management"
description: "PROJECT_CONTEXT, handoff, ADR — chống agent drift — cohort 1 & 2"
weight: 4
---

# Context Management — chống agent drift

## Vấn đề

AI agent (Claude Code, Cursor, Codex...) mỗi session đọc lại codebase. Không có
context file → agent tự khám phá → dễ hallucinate, dùng doc cũ, lặp quyết định sai.
9/12 đội Cohort 1 không có context-management layer.

## Pattern 1: PROJECT_CONTEXT.md — Quick Rehydrate (team 001 Memio)

File agent đọc ĐẦU TIÊN khi resume. Mục tiêu: < 60 giây để agent "lên dây".

```markdown
## 0. Quick Rehydrate (≤ 60s)
- Project: [tên] — [1 câu]
- Stack: Python / FastAPI / LangGraph
- Dev: uvicorn src.main:app --reload
- Test: make test. Eval: python eval/run_eval.py

## 0.1 Current Invariants (để không drift)
- Source of truth kỹ thuật: code trong src/. Doc chỉ tóm tắt — CODE WINS.
- Agent flow: src/agents/graph.py.

## 0.2 Known Ambiguities / Mismatches
- [liệt kê chỗ doc-vs-code lệch]
```

Tại sao hiệu quả: agent biết ngay source-of-truth ở đâu → không drift; mục
"Known Ambiguities" (team 011) ngăn agent tin doc stale.

## Pattern 2: Handoff low-token (team 001)

Khi chuyển session/người, ghi `handoff/SESSION_NOTES.md`:

```markdown
## Handoff — [date] — [người]
**Đang giữa**: [1 câu]
**Files đã chạm** (5-15):
- path/file1.py — [thay đổi]
**Bước tiếp theo**: [1 câu]
**Blocker**: [nếu có]
```

Quy tắc: CHỈ 5-15 file quan trọng nhất, KHÔNG dump diff. Tiết kiệm token khi
agent resume.

## Pattern 3: ADR trong WORKLOG (team 010)

Mỗi quyết định kỹ thuật lớn ghi theo format ADR (Architecture Decision Record):

```markdown
### [ADR-001] — Mock-first LLM — [date]
**Context**: Sinh viên cần test flow khi chưa có API key.
**Options**:
- A: bắt buộc key → friction cao.
- B: mock khi thiếu key → friction thấp, output không thật.
**Decision**: B.
**Consequences**: (+) chạy được ngay; (−) phải set key khi muốn output thật.
```

ADR giúp agent sau hiểu VÌ SAO code hiện tại như vậy — không chỉ WHAT. Đây là
pattern ít đội làm nhưng rất có giá trị.

## Pattern 4: Tách template khỏi instance (team 001)

`docs/templates/JOURNAL.template.md` riêng — JOURNAL.md instance không lặp template
→ token-clean.

## Tham khảo template

`ai20k-agent-template`: `PROJECT_CONTEXT.md`, `handoff/`, `WORKLOG.md` mục ADR.
