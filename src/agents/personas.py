"""Persona registry — agent behaviour as DATA, không phải code (C1, inspire team 002).

Thay vì hardcode tính cách agent trong if/else, mô tả persona bằng frozen dataclass.
Lợi ích:
- Dễ A/B test (chỉ đổi persona config).
- Dễ mở rộng (thêm persona = thêm 1 entry).
- Immutable (`frozen=True`) → không ai vô tình sửa runtime.

Ví dụ này là optional advanced — sinh viên có thể bỏ qua nếu app không cần persona.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Persona:
    """Một persona agent. Frozen → immutable."""

    name: str
    description: str
    temperature: float  # sáng tạo cao hơn / thấp hơn tuỳ persona
    tone_rules: str


# Registry — single source of truth cho persona. Inspire team 002.
PERSONAS: dict[str, Persona] = {
    "default": Persona(
        name="default",
        description="Trợ lý trung lập, chính xác.",
        temperature=0.3,
        tone_rules="Lịch sự, ngắn gọn, đúng trọng tâm.",
    ),
    "mentor": Persona(
        name="mentor",
        description="Người hướng dẫn kiên nhẫn, gợi mở.",
        temperature=0.5,
        tone_rules="Đặt câu hỏi gợi ý trước khi đưa đáp án. Khích lệ.",
    ),
    "concise": Persona(
        name="concise",
        description="Trợ lý siêu ngắn gọn.",
        temperature=0.2,
        tone_rules="Tối đa 3 câu. Không giải thích thừa.",
    ),
}


def get_persona(name: str = "default") -> Persona:
    """Lấy persona theo tên. Fallback về default nếu không có."""
    return PERSONAS.get(name, PERSONAS["default"])
