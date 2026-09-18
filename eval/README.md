# Evaluation Framework (C3)

Template này có eval framework hoàn chỉnh (inspire team 008 Buddy + 009 VibeMaster
+ 011 CareerPulse). Chạy được mock-first (không cần API key).

## Files

| File | Vai trò |
|---|---|
| `golden_dataset.yaml` | Dataset 10 cases (happy / ambiguous / safety / citation / injection / robustness) |
| `run_eval.py` | Runner — chạy agent trên mỗi case, auto-check deterministic |
| `judge.py` | LLM-as-Judge — chấm faithfulness/helpfulness/safety/citation (1-5) |
| `cost_benchmark.py` | Ước chi phí chạy eval trên các model |
| `thresholds.yaml` | Gate: pass_rate ≥ 80%, judge avg ≥ 4.0, safety 0 fail |
| `results/<ts>/` | Output mỗi đợt: report.md + cases.json + judge_input.jsonl |

## Chạy

```bash
# 1. Cài pyyaml
pip install pyyaml

# 2. Chạy eval (mock-first)
python eval/run_eval.py

# 3. (optional) LLM-as-Judge — cần OPENAI_API_KEY
python eval/judge.py eval/results/<ts>/judge_input.jsonl

# 4. Ước chi phí
python eval/cost_benchmark.py
```

## Mở rộng

- Thêm case vào `golden_dataset.yaml` theo category (safety, citation, injection...).
- Thay auto-check trong `run_eval._check` nếu cần rule riêng.
- Khi setup vector store thật, cập nhật `retrieve_node` — eval sẽ tự đối chiếu citation.

## Tại sao quan trọng

- Cohort 1: chỉ 2/12 teams có evaluation evidence → mất điểm BTC.
- Eval framework = bằng chứng testing cho Demo Day + regression safety khi đổi prompt/model.
