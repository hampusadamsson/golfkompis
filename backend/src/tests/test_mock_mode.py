# pyright: reportPrivateUsage=false
"""Tests for MOCK mode: dev/test deployments must never contact external parties."""

from pytest import MonkeyPatch

from golfkompis.config import settings
from golfkompis.mingolf import MinGolf
from golfkompis.mock_client import FakeMinGolf
from golfkompis.queue.worker import _login_sync


def test_login_sync_returns_fake_client_in_mock_mode(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "mock", True)
    golf = _login_sync("19900101-1234", "whatever")
    assert isinstance(golf, FakeMinGolf)


def test_login_sync_returns_real_client_outside_mock_mode(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "mock", False)

    called = False

    def fake_login(self: MinGolf, username: str, password: str) -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(MinGolf, "login", fake_login)
    golf = _login_sync("19900101-1234", "whatever")
    assert called
    assert type(golf) is MinGolf


def test_fake_client_login_is_noop() -> None:
    fake = FakeMinGolf()
    fake.preload()
    # must not raise or make any HTTP call for arbitrary credentials
    fake.login("19900101-1234", "not-a-real-password")
