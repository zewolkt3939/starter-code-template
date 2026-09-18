"""Cost benchmark (C3) — inspire team 008 (Buddy run_cost_benchmark.py).

Ước lượng chi phí chạy eval trên các model khác nhau, giúp chọn model value.
Dựa trên price profile ($/1M token) × số token ước lượng/case.

Mock-first: chỉ tính toán, không gọi API.
"""

from __future__ import annotations

# Price profile USD / 1M tokens (giá approximation, update theo vendor).
PRICE_PROFILE = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gemini-2.5-flash": {"input": 0.075, "output": 0.30},
}

# Ước lượng token/case (system prompt + context + output).
EST_TOKENS = {"input": 1500, "output": 200}
N_CASES = 10


def estimate(model: str, n_cases: int = N_CASES) -> float:
    p = PRICE_PROFILE[model]
    cost_in = EST_TOKENS["input"] * n_cases * p["input"] / 1_000_000
    cost_out = EST_TOKENS["output"] * n_cases * p["output"] / 1_000_000
    return round(cost_in + cost_out, 4)


if __name__ == "__main__":
    print(f"{'Model':<20} {'Cost/run (USD)':<16} {'Cost/1000 runs'}")
    for m in PRICE_PROFILE:
        c = estimate(m)
        print(f"{m:<20} ${c:<15} ${c * 1000}")
