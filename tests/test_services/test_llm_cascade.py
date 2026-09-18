"""Test cascade router — model rẻ cho task rẻ, model mạnh cho task mạnh."""

import pytest

from src.config import get_settings
from src.services.llm import get_llm


@pytest.fixture(autouse=True)
def _fresh_settings(monkeypatch):
    """Mỗi test đọc lại Settings từ env — không dính cache của test khác."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("MODEL_CLASSIFY", "gpt-4o-mini")
    monkeypatch.setenv("MODEL_GENERATE", "gpt-4o")
    monkeypatch.setenv("MODEL_JUDGE", "gpt-4o-mini")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_classify_uses_cheap_model():
    assert get_llm("classify").model_name == "gpt-4o-mini"


def test_generate_uses_strong_model():
    assert get_llm("generate").model_name == "gpt-4o"


def test_judge_uses_configured_model():
    assert get_llm("judge").model_name == "gpt-4o-mini"


def test_judge_same_model_as_generator_raises():
    get_settings.cache_clear()
    import os
    os.environ["MODEL_JUDGE"] = "gpt-4o"  # trùng MODEL_GENERATE
    get_settings.cache_clear()
    with pytest.raises(ValueError, match="self-preference"):
        get_llm("judge")
    os.environ.pop("MODEL_JUDGE")


def test_classify_and_judge_run_at_low_temperature():
    settings = get_settings()
    settings.llm_temperature = 0.9  # generate có thể nóng
    assert get_llm("classify").temperature == 0.0
    assert get_llm("judge").temperature == 0.0
    assert get_llm("generate").temperature == 0.9
