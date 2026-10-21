"""Command-line behaviour: output, exit codes and secret hygiene."""

from __future__ import annotations

import json

import pytest

from src import main as cli
from tests.fakes import FAKE_API_KEY, FakeAnthropicAPI, error_body, message_body, respond, text_block

GOOD_REPLY = '{"category": "billing", "confidence": 0.88, "explanation": "Asks about a double charge."}'


@pytest.fixture
def fake_api(monkeypatch):
    """Configure a fake key and route the CLI's client through a fake API."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", FAKE_API_KEY)

    def install(handler) -> FakeAnthropicAPI:
        api = FakeAnthropicAPI(handler)
        monkeypatch.setattr(cli, "create_client", lambda settings: api.client(settings))
        return api

    return install


def test_classify_prints_json_and_exits_zero(fake_api, capsys):
    fake_api(respond(200, message_body(text_block(GOOD_REPLY))))

    exit_code = cli.main(["classify", "I", "was", "charged", "twice"])

    captured = capsys.readouterr()
    assert exit_code == cli.EXIT_OK
    assert json.loads(captured.out) == {
        "category": "billing",
        "confidence": 0.88,
        "explanation": "Asks about a double charge.",
    }


def test_classify_prompts_for_text_when_no_argument(fake_api, monkeypatch, capsys):
    api = fake_api(respond(200, message_body(text_block(GOOD_REPLY))))
    monkeypatch.setattr("builtins.input", lambda prompt: "I was charged twice")

    assert cli.main(["classify"]) == cli.EXIT_OK
    assert "I was charged twice" in api.last_json["messages"][0]["content"]


def test_classify_without_key_exits_with_config_error(capsys):
    exit_code = cli.main(["classify", "hello"])

    captured = capsys.readouterr()
    assert exit_code == cli.EXIT_CONFIG
    assert "ANTHROPIC_API_KEY is not configured" in captured.err
    assert "No request was sent" in captured.err
    assert captured.out == ""


def test_classify_reports_invalid_model_json(fake_api, capsys):
    fake_api(respond(200, message_body(text_block("billing"))))

    exit_code = cli.main(["classify", "I was charged twice"])

    assert exit_code == cli.EXIT_FAILURE
    assert "could not be used" in capsys.readouterr().err


def test_auth_failure_exits_one_without_printing_key(fake_api, capsys):
    fake_api(respond(401, error_body("authentication_error", "invalid x-api-key")))

    exit_code = cli.main(["ping"])

    captured = capsys.readouterr()
    assert exit_code == cli.EXIT_FAILURE
    assert "HTTP 401" in captured.err
    assert FAKE_API_KEY not in captured.out + captured.err


def test_ping_prints_reply_and_usage(fake_api, capsys):
    fake_api(respond(200, message_body(text_block("The API test call worked."))))

    exit_code = cli.main(["ping"])

    out = capsys.readouterr().out
    assert exit_code == cli.EXIT_OK
    assert "Reply : The API test call worked." in out
    assert "Tokens: 42 input / 17 output" in out


def test_check_env_works_without_credentials(capsys):
    exit_code = cli.main(["check-env"])

    out = capsys.readouterr().out
    assert exit_code == cli.EXIT_OK
    assert "Python version" in out
    assert "anthropic" in out
    assert "ANTHROPIC_API_KEY : not configured" in out


def test_check_env_hides_configured_key(monkeypatch, capsys):
    monkeypatch.setenv("ANTHROPIC_API_KEY", FAKE_API_KEY)

    cli.main(["check-env"])

    out = capsys.readouterr().out
    assert "configured (value hidden)" in out
    assert FAKE_API_KEY not in out
