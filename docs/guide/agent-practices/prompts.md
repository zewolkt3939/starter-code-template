---
title: "Prompt Engineering"
description: "Structured XML prompts, SAFEGUARDS, citation contract — từ cohort 1 & 2"
weight: 1
---

# Prompt Engineering

## Bài học từ cohort

3/12 đội (002 DevCoach, 004 MeeA, 007 Activation Engine) viết prompt theo cấu trúc
XML rõ ràng → output ổn định, dễ debug. Các đội còn lại dùng prompt 1-2 dòng generic
→ output lệch, mất điểm.

## Pattern 1: Structured XML tags

**Bad** (đa số đội yếu):
```text
You are a helpful assistant. Answer the user's question.
```

**Good** (team 002, 004):
```xml
<role>
Bạn là AI20K Agent — trợ lý chính xác, đúng sự thật.
</role>

<context>
Bạn nhận Context từ knowledge base qua RAG. Ưu tiên Context.
</context>

<instructions>
1. Đọc Context trước.
2. Mỗi nhận định kèm [cite:chunk_id].
3. Output đúng JSON schema.
</instructions>

<rules>
- Tiếng Việt có dấu.
- Không bịa khi thiếu dẫn chứng.
</rules>

<output_format>
{ "verdict": "...", "answer": "...", "citation_ids": [...] }
</output_format>

<verification>
Trước khi trả, kiểm tra: citation có thật không? verdict nhất quán?
</verification>
```

Tại sao hiệu quả: mỗi section có vai trò riêng, LLM dễ tuân theo; section
`<verification>` ép agent tự check trước khi output (giảm hallucination).

## Pattern 2: SAFEGUARDS tách bạch (team 005 NestAI)

KHÔNG pha rule an toàn vào personality. Tách section riêng:

```text
<safeguards>
KHẨN CẤP: nếu user nhắc dấu hiệu nguy hiểm (ra máu, khó thở...),
đưa CẢNH BÁO ĐỎ, KHÔNG tư vấn chung.
KHÔNG bịa liều lượng thuốc.
</safeguards>
```

## Pattern 3: External prompt files (team 004 MeeA)

Lưu prompt ở `prompts/*.md` với `{{placeholder}}`, KHÔNG nhúng Python string:

```markdown
<role>...</role>
<context>{{context}}</context>
```

Loader (`src/agents/prompts.py`): `@lru_cache` + `str.replace`. Lợi ích: đổi prompt
không cần deploy code; mentor review được; diff git rõ.

## Pattern 4: SHARED_RULES DRY (team 002)

Rule chung (tiếng Việt, độ dài câu...) thành 1 constant inject vào nhiều prompt —
tránh lặp.

## Anti-pattern (tránh)

- "Be helpful" generic → cụ thể hoá: "Be specific about output format".
- "Don't hallucinate" → "Only reference chunks listed in Context".
- Nhúng số liệu cứng vào prompt → để trong reference file.

## Tham khảo template

Xem `prompts/system_prompt.md`, `safeguards.md`, `citation_rules.md` trong
`ai20k-agent-template`.
