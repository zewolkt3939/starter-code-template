#!/usr/bin/env python3
"""Doc-code sync checker cho ai20k-technical-guidebook (WP0.4).

Chạy: python3 scripts/check_docs.py
Exit 0 = PASS, exit 1 = có lỗi. Dùng trong CI (.github/workflows/doc-check.yml)
hoặc chạy local trước khi commit.

3 nhóm check:
1. LINK — mọi link relative trong content/docs/*.md trỏ tới file/thư mục tồn tại thật
2. MODEL — không còn model deprecated (gpt-3.5-turbo...) trong code mẫu / env mẫu
3. PATH — mọi path template mà guidebook nhắc (Makefile, requirements.txt...) tồn tại
   trong ../ai20k-agent-template (nếu repo đó có mặt — local dev / monorepo checkout)
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs" / "guide"
TEMPLATE = ROOT


DEPRECATED_MODELS = [
    "gpt-3.5-turbo",       # retired — thay bằng gpt-4o-mini/gpt-4.1
    "text-davinci-003",
]
# Path trong template mà guidebook được phép nhắc (file thật phải tồn tại)
TEMPLATE_PATHS = [
    "src/agents/guardrails.py", "src/agents/nodes/human_review_node.py",
    "eval/run_eval.py", "pytest.ini",
    "Makefile", "requirements.txt", "Dockerfile", "docker-compose.yml",
    ".env.example", "ruff.toml", "src/main.py", "src/config.py",
    "src/agents/graph.py", "src/agents/state.py",
]

errors: list[str] = []

# ---- 1. LINK check ----
md_files = sorted(DOCS.rglob("*.md"))
link_re = re.compile(r"\]\(([^)#\s]+)(?:#[^)\s]*)?\)")
fence_re = re.compile(r"```.*?```", re.DOTALL)


def prose_only(text: str) -> str:
    """Bỏ fenced code blocks — link regex không được quét code
    (tránh false positive kiểu `_SAFE_FUNCTIONS[name](*args)`)."""
    return fence_re.sub("", text)


checked = 0
for md in md_files:
    for m in link_re.finditer(prose_only(md.read_text(encoding="utf-8"))):
        href = m.group(1)
        if href.startswith(("http://", "https://", "mailto:", "hook://")):
            continue
        target = (md.parent / href).resolve()
        checked += 1
        if not target.exists():
            errors.append(f"LINK broken [{md.relative_to(ROOT)}] -> {href}")

# ---- 2. MODEL check (trừ dòng có chú thích retire — cho phép NHẮC rằng đã retire) ----
for md in md_files:
    text = md.read_text(encoding="utf-8")
    for model in DEPRECATED_MODELS:
        for m in re.finditer(re.escape(model), text):
            start = max(0, m.start() - 80)
            ctx = text[start:m.end() + 80]
            ctx_l = ctx.lower()
            if "retire" in ctx_l or "deprecated" in ctx_l or "không dùng" in ctx_l:
                continue  # được phép nhắc kèm cảnh báo retire
            errors.append(f"MODEL deprecated [{md.relative_to(ROOT)}]: {model}")

# ---- 3. PATH check (chỉ khi template repo có mặt cạnh guidebook) ----
if TEMPLATE.is_dir():
    for rel in TEMPLATE_PATHS:
        if not (TEMPLATE / rel).exists():
            errors.append(f"PATH template thiếu: {rel} (guidebook có nhắc tới)")
else:
    print("NOTE: ai20k-agent-template không nằm cạnh guidebook — bỏ qua PATH check.")

# ---- Report ----
print(f"Checked {len(md_files)} md files, {checked} internal links.")
if errors:
    print(f"\n❌ {len(errors)} lỗi:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
print("✅ doc-check PASS — links, models, template paths đều khớp.")
