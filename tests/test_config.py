from src.config import Settings


def test_agent_max_iterations_default_matches_env_example():
    assert Settings(_env_file=None).agent_max_iterations == 8


def test_env_example_value_is_accepted(monkeypatch):
    monkeypatch.setenv("AGENT_MAX_ITERATIONS", "8")
    assert Settings(_env_file=None).agent_max_iterations == 8
