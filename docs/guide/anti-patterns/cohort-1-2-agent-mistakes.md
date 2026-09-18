---
title: "Cohort 1 & 2 — Agent Practice Mistakes"
description: "Sai lầm về agent engineering từ 12 đội — PHẢI TRÁNH"
weight: 2
---

# Cohort 1 & 2 — Agent Engineering Mistakes

Bổ sung cho [Common Mistakes](common-mistakes.md) (code quality). Phần này là
**agent-practice** anti-pattern — lỗi về cấu hình AI agent, prompt, eval, guardrail.

## 1. Hardcoded absolute path — team 005

```json
// ❌ Gãy khi move repo / share team
"command": "python /Users/huyenchu/A20-App-005/scripts/log_hook.py"
```

```json
// ✅ Dùng biến môi trường / relative path
"command": "bash scripts/_pyrun.sh scripts/log_hook.py --tool=claude"
```

## 2. `.bak` vô hiệu hoá hooks — team 007

`.claude/settings.json.bak` → hook TẮT, AI logging không chạy, mất dấu vết dùng AI.
Nếu muốn tắt tạm, comment có lý do + reminder bật lại. Đừng rename `.bak`.

## 3. Stub code không dùng gây nhầm — team 005, 006, 008

`src/agent.py` boilerplate generic ("You are a helpful assistant") KHÔNG được dùng,
trong khi agent thật ở `src/retrieval/agent.py`. AI tool đọc codebase sẽ nhầm
"đâu là agent thật".

→ Xoá stub, hoặc ghi rõ `# DEPRECATED — real agent ở src/...`.

## 4. Silent fallback — team 002

```python
# ❌ Che regression
except Exception:
    logger.exception("...")
    return default  # AI chạy trên/regression mà không ai biết
```

Team 002 phải viết `ROOT_CAUSE_ANALYSIS.md` cho bug này. Log + đánh dấu FAILED,
không return default lặng lẽ.

## 5. Triplicate workflow — team 008

Cùng `feature-planner` nhân ra `.claude/commands/` + `.codex/skills/` +
`.github/prompts/` → 3 chỗ phải sửa đồng bộ, dễ lệch.

→ 1 source of truth, generate/symlink ra các tool.

## 6. Không có eval framework — 10/12 đội

Chỉ `eval/results/report.md` blank placeholder. → Mất điểm Evaluation Evidence.
→ Dùng `eval/` framework trong template (golden dataset + runner + judge).

## 7. Guardrail 1 lớp — 11/12 đội

Chỉ prompt safeguard, không có code guardrail → jailbreak bypass. → Defence-in-depth.

## 8. Permission quá permissive — team 002

`.claude/settings.local.json` auto-allow `Bash(python *)`, `Bash(git commit *)`,
`Bash(rm -v ...)`. Nguy hiểm nếu share. → Curated allow + deny rõ ràng.

## 9. Không citation contract — 9/12 đội

Agent trả lời không kèm nguồn → user không verify → mất điểm credibility. →
`[cite:chunk_id]` contract.

## 10. Doc stale mà không flag — 9/12 đội

PRD/docs nói Node/Gemini nhưng code đã FastAPI/OpenAI → agent tin doc → code sai.
→ Mục "Known Ambiguities" trong PROJECT_CONTEXT (team 011).

---

> Mỗi anti-pattern trên đều có **pattern đúng** ở phần
> [Agent Engineering Practices](../agent-practices/). Đọc đối chiếu.
