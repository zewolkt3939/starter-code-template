---
title: "Multi-Tool Config"
description: ".claude/.codex/.gemini mirror, permissions, scope-guard — cohort 1 & 2"
weight: 5
---

# Multi-Tool Agent Config

## Vấn đề

Đội dùng nhiều AI tool (Claude Code, Cursor, Codex, Gemini, Copilot, Antigravity).
Mỗi tool có cấu hình khác nhau. Không chuẩn hoá → logging thiếu, quyền nguy hiểm,
agent config rời rạc.

## Pattern 1: Logging hooks đa-tool (baseline — 12/12 đội)

Mỗi tool có file hook riêng gọi chung `scripts/log_hook.py`:
- `.claude/settings.json` — Claude Code
- `.cursor/hooks.json` — Cursor
- `.codex/hooks.json` — Codex CLI
- `.gemini/settings.json` — Gemini CLI
- `.github/hooks/hooks.json` — Copilot

Antigravity không có hook system → dùng `.agent/rules/logging.md` (rule file) bù.

## Pattern 2: Defensive `|| true` (team 003)

Hook log KHÔNG được block agent khi server fail:

```json
"command": "bash scripts/_pyrun.sh scripts/log_hook.py --tool=claude 2>/dev/null || true"
```

`2>/dev/null || true` → nếu log server chết, agent vẫn chạy. Chỉ team 003 làm —
nên áp dụng rộng rãi.

## Pattern 3: Triple mirror theo strength tool (team 011 CareerPulse)

Mỗi tool-ecosystem có entry riêng được tuning cho thế mạnh:
- `.claude/` — tracing / validation
- `.codex/` — implementation
- `.gemini/` — review / phân tích mâu thuẫn doc-vs-code

Cùng rule được nhân ra, mỗi bản nhấn mạnh điểm mạnh tool. Đây là pattern nâng cao.

## Pattern 4: Permissions allow + deny (team 011)

`.claude/settings.json` với deny list curated theo risk project:

```json
"deny": [
  "Read(.env)",
  "Read(**/*credential*)",
  "Bash(rm -rf:*)",
  "Bash(git push --force:*)",
  "Bash(sudo:*)",
  "Bash(* --no-verify*)"
]
```

Tại sao: chặn agent vô tình lộ secret / xoá file / bypass hook.

## Pattern 5: Scope-guard hook (team 009 VibeMaster)

Bash hook chặn lệnh thoát scope repo:

```bash
BLOCKED_PATTERNS=(
  'cd[[:space:]]+\.\./'      # thoát repo
  'rm[[:space:]]+-rf[[:space:]]+/'
  'sudo[[:space:]]'
)
# match → exit 2 (block tool)
```

## Pattern 6: Slash commands + subagents (team 008, 009)

`.claude/commands/feature.md` — workflow có approval gate ("Ready to implement?
Proceed?"). `.claude/agents/code-reviewer.md` — subagent review diff. Biến Claude
Code thành orchestrator có cấu trúc, không phải chat tự do.

## Pattern 7: PR template với Harness Verification (team 003)

`.github/pull_request_template.md` bắt dev xác nhận `make lint` / `make test` /
`eval pass` / logging còn hoạt động. Bridge agent verification và human review.

## Anti-pattern (tránh)

- Hardcoded absolute path (`/Users/xxx/...`) — gãy khi move repo (team 005 lỗi).
- File `.bak` vô hiệu hoá hooks (team 007 lỗi).
- Cùng workflow nhân 3 file giống nhau — DRY (team 008 lỗi).

## Tham khảo template

`ai20k-agent-template`: `.claude/` (settings/commands/agents/skills/hooks),
`.github/pull_request_template.md`, `.agents/rules/`.
