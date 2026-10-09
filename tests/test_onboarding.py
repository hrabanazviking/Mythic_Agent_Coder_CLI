"""Slice 34 tests: onboarding tutorial and setup verification."""

from pathlib import Path

from mythic_agent import onboarding


def _make_io(answers):
    """Build (input_fn, output_fn) stubs; answers feeds the prompts."""
    it = iter(answers)
    seen = []

    def input_fn(prompt=""):
        seen.append(prompt)
        return next(it)

    def output_fn(text):
        seen.append(text)

    return input_fn, output_fn, seen


def test_tutorial_completes_with_enter_only():
    input_fn, output_fn, seen = _make_io([""] * (len(onboarding.tutorial_steps()) + 2))
    result = onboarding.run_tutorial(input_fn=input_fn, output_fn=output_fn)
    assert result["completed"] is True
    assert any("Mythic Agent" in line for line in seen if isinstance(line, str))


def test_tutorial_quits_early_on_q():
    input_fn, output_fn, _ = _make_io(["q"])
    result = onboarding.run_tutorial(input_fn=input_fn, output_fn=output_fn)
    assert result["completed"] is False


def test_tutorial_captures_provider_and_model():
    steps = len(onboarding.tutorial_steps())
    answers = [""] * steps + ["https://example.com/v1", "my-model"]
    input_fn, output_fn, _ = _make_io(answers)
    config: dict = {}
    result = onboarding.run_tutorial(input_fn=input_fn, output_fn=output_fn, config=config)
    assert result["completed"] is True
    assert config["base_url"] == "https://example.com/v1"
    assert config["model"] == "my-model"


def test_tutorial_steps_cover_essentials():
    titles = [title for title, _ in onboarding.tutorial_steps()]
    assert len(titles) >= 5
    joined = " ".join(titles).lower()
    assert "chat" in joined


def test_check_setup_flags_missing_model(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("MYTHIC_HOME", str(tmp_path / ".mythic"))
    for name in ("MYTHIC_API_KEY", "OPENAI_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    issues = onboarding.check_setup(config={"model": "", "base_url": ""})
    codes = {issue.code for issue in issues}
    assert "no_model" in codes
    assert "no_base_url" in codes


def test_check_setup_healthy_config_passes(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("MYTHIC_HOME", str(tmp_path / ".mythic"))
    monkeypatch.setenv("MYTHIC_API_KEY", "test-key")
    issues = onboarding.check_setup(config={"model": "x", "base_url": "https://example.com"})
    assert isinstance(issues, list)
    assert "no_model" not in {i.code for i in issues}
