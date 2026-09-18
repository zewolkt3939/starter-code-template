"""Prompt loader + SHARED_RULES (C2).

Pattern:
- `load_prompt(name)` đọc file `.md` từ `prompts/`, cache bằng `@lru_cache` để không
  đọc disk nhiều lần (inspire team 003).
- `SHARED_RULES` là constant inject vào nhiều prompt — DRY cho prompt engineering
  (inspire team 002 SHARED_VOICE_RULES).
- `build_system_prompt()` render `{{placeholder}}` — pattern external prompt file
  (inspire team 004).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

_PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"

# Rules chung inject vào mọi prompt (DRY). Inspire team 002 SHARED_VOICE_RULES.
SHARED_RULES = """- Trả lời tiếng Việt có dấu.
- Không pha tiếng Anh không cần thiết; nếu dùng thuật ngữ Anh, giữ nguyên trong ngoặc.
- Ngắn gọn, đúng trọng tâm. Không lặp ý.
- Khi không chắc → nói "tôi không chắc", không bịa."""


@lru_cache(maxsize=16)
def load_prompt(name: str) -> str:
    """Đọc prompt file, cache kết quả. Raise FileNotFoundError nếu thiếu."""
    path = _PROMPTS_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Prompt file không tồn tại: {path}")
    return path.read_text(encoding="utf-8")


def build_system_prompt() -> str:
    """Render system_prompt.md với placeholder substituted."""
    safeguards = load_prompt("safeguards.md")
    # Bọc citation_rules vào shared block
    try:
        citation = load_prompt("citation_rules.md")
        shared = SHARED_RULES + "\n\n" + citation
    except FileNotFoundError:
        shared = SHARED_RULES

    return load_prompt("system_prompt.md").replace("{{shared_rules}}", shared).replace("{{safeguards}}", safeguards)
