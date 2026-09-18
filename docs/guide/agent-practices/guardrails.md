---
title: "Guardrails & Anti-Hallucination"
description: "Defence-in-depth, verbatim sacred, conservative bias — cohort 1 & 2"
weight: 3
---

# Guardrails & Anti-Hallucination

## Bài học từ cohort

Prompt safeguard ĐỘC THÂN — LLM có thể bị jailbreak bỏ qua. Đội 005 (NestAI) đặt
guardrail ở **cả prompt LẪN code** → an toàn hơn hẳn. Đội 012 (ARAS) có rule
"verbatim is sacred" → chống bịa số liệu học thuật.

## Pattern 1: Defence-in-depth (team 005 NestAI)

2 lớp độc lập:

**Lớp 1 — prompt** (`prompts/safeguards.md`):
```text
<safeguards>
KHẨN CẤP: dấu hiệu nguy hiểm → cảnh báo đỏ, không tư vấn chung.
</safeguards>
```

**Lớp 2 — code** (`nodes/safety_node.py`): check `DANGER_KEYWORDS` TRƯỚC khi qua LLM.
```python
DANGER_KEYWORDS = ("ra máu", "khó thở", "tự hại", ...)
if any(kw in query for kw in DANGER_KEYWORDS):
    return {"bypass": True, "response": DANGER_RESPONSE}
```

Nếu LLM bị jailbreak bỏ qua lớp prompt, lớp code vẫn chặn. Đây là pattern quan
trọng NHẤT cho app y tế / pháp lý / tài chính.

## Pattern 2: Verbatim is sacred (team 012 ARAS)

Khi agent trích dẫn dữ liệu/số liệu:
```text
- KHÔNG làm tròn số.
- KHÔNG diễn giải lại.
- KHÔNG đổi đơn vị.
- Trích nguyên văn từ nguồn.
```
Vì sao: làm tròn số liệu học thuật = fabrication, hậu quả nghiêm trọng.

## Pattern 3: Conservative bias (team 012)

Khi không đủ dẫn chứng → `verdict: "uncertain"`, KHÔNG claim "supported".
```text
Thà thiếu thông tin còn hơn bịa.
```

Áp dụng trong schema (`models/schemas.py`):
```python
class AgentAnswer(BaseModel):
    verdict: Literal["supported", "partially_supported", "unsupported", "uncertain"]
    confidence: float = Field(ge=0.0, le=1.0)
    citation_ids: list[str]
    def is_safe(self) -> bool:
        if self.verdict != "uncertain" and not self.citation_ids:
            return False  # claim mà không cite = unsafe
        ...
```

## Pattern 4: Output schema-lock (team 009, 012)

Đừng chỉ yêu cầu JSON trong prompt — validate lại bằng Pydantic ở code. Double
validation: prompt + schema.

## Pattern 5: "Source code wins" (team 011)

Rule cho agent khi code:
```text
Khi doc mâu thuẫn code → tin CODE.
Ghi mismatch vào PROJECT_CONTEXT Known Ambiguities, KHÔNG "sửa" doc theo giả định.
```

## Anti-pattern: silent fallback (team 002 root-cause)

```python
# ❌ Silent — che lỗi
try:
    result = await llm()
except Exception:
    return default_answer  # AI running trên/regression mà không ai biết
```

```python
# ✅ Log + đánh dấu
except Exception as e:
    logger.exception("llm failed")
    return {"error": str(e), "quality_result": {"status": "FAILED"}}
```

Đội 002 đã viết `ROOT_CAUSE_ANALYSIS.md` cho bug này — hãy học từ họ.
