import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_judge_script_imports_from_repo_root():
    # Chạy đúng như docstring hướng dẫn: `python eval/judge.py` từ repo root.
    proc = subprocess.run(
        [sys.executable, "eval/judge.py"], cwd=ROOT, capture_output=True, text=True
    )
    assert "ModuleNotFoundError" not in proc.stderr
    assert proc.returncode == 2  # thiếu argument -> in Usage
