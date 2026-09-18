---
title: "Agent Engineering Practices"
description: "Good practices từ Cohort 1 & 2 — prompts, evals, guardrails, multi-tool config"
weight: 7
---

# Agent Engineering Practices — bài học từ 12 đội Cohort 1 & 2

Phần này tổng hợp các **good practices** về agent engineering rút ra từ việc phân tích
12 repo đội Cohort 1 & 2. Đây là những pattern thực chiến giúp đội đạt điểm cao ở
các tiêu chí AI Agent, Code Quality và Evaluation Evidence.

> Mỗi practice đều kèm **bằng chứng cohort** ("X/12 đội đã làm") và **before/after**,
> để bạn hiểu VÌ SAO chứ không chỉ HOW.

> 📄 **Xem bản tổng hợp one-page** (cả template + guidebook + anti-patterns +
> inspiration map): [Báo cáo tổng hợp Cohort 3](https://github.com/hailoc12/ai20k-agent-template/blob/main/docs/COHORT3_REPORT.md).

## Trang trong mục này

- [Prompt Engineering](prompts.md) — XML structure, SAFEGUARDS, citation, external files
- [Evaluation Framework](evals.md) — golden dataset, runner, LLM-as-Judge, cost benchmark
- [Guardrails & Anti-Hallucination](guardrails.md) — defence-in-depth, verbatim sacred
- [Context Management](context-management.md) — PROJECT_CONTEXT, handoff, ADR
- [Multi-Tool Config](multi-tool-config.md) — .claude/.codex/.gemini mirror, permissions

## Tổng quan nhanh

| Pattern | Đội làm tốt | Đội bỏ sót | Hậu quả bỏ sót |
|---|---|---|---|
| Structured XML prompt | 002, 004, 007 | đa số | Output không ổn định, khó debug |
| Eval framework | 002, 008, 009, 011 | 10/12 | Mất điểm Evaluation Evidence |
| Defence-in-depth guardrail | 005, 007 | 11/12 | Jailbreak bypass safeguard |
| PROJECT_CONTEXT | 001, 008, 011 | 9/12 | Agent drift, hallucinate doc cũ |
| Citation contract | 006, 009, 012 | 9/12 | User không verify nguồn |

Đọc theo thứ tự trên. Mỗi trang ~5-10 phút.
