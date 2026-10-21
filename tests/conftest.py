"""Shared fixtures. Every test runs offline and ignores the developer's real credentials."""

from __future__ import annotations

import socket

import pytest

from src import api_client
from src.api_client import ClaudeSettings
from tests.fakes import FAKE_API_KEY

_CONFIG_ENV_VARS = (
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_BASE_URL",
    "ANTHROPIC_PROFILE",
    "CLAUDE_MODEL",
    "CLAUDE_USE_FALLBACKS",
)


@pytest.fixture(autouse=True)
def isolated_config(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """Hide real environment variables and the real .env file from every test."""
    for name in _CONFIG_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(api_client, "DEFAULT_ENV_FILE", tmp_path / "no-such.env")


@pytest.fixture(autouse=True)
def block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail loudly if any code path tries to open a real network connection."""

    def refuse(*args, **kwargs):
        raise RuntimeError("Tests must not open network connections.")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)


@pytest.fixture
def settings() -> ClaudeSettings:
    return ClaudeSettings(api_key=FAKE_API_KEY)
