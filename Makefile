.PHONY: run test lint format typecheck eval check clean

run:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v

# Eval regression — chạy agent qua golden dataset, judge tách generator,
# xuất eval/results/report.md (good practice #8/#9: team 002 + 008).
# Không cần API key (offline stub mode); có key là chạy LLM thật.
eval:
	python3 eval/run_eval.py

eval-strict:
	python3 eval/run_eval.py --strict

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/

typecheck:
	mypy src/

check: lint format test

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .ruff_cache -exec rm -rf {} +
