"""Tests for email templates and send functions."""

import pathlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = (
    pathlib.Path(__file__).parent.parent
    / "golfkompis"
    / "users"
    / "templates"
    / "email"
)
FAKE_URL = "https://example.com/verify?token=abc123"


@pytest.fixture
def jinja_env() -> Environment:
    return Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=True)


def _render(env: Environment, template_name: str, url: str = FAKE_URL) -> str:
    return env.get_template(template_name).render(url=url)


def test_verification_template_renders(jinja_env: Environment) -> None:
    html = _render(jinja_env, "verification.html")
    assert FAKE_URL in html
    assert html.count(FAKE_URL) >= 2  # button href + fallback link
    assert "{{" not in html
    assert "{%" not in html
    assert "<script" not in html
    assert "Bekräfta" in html


def test_reset_template_renders(jinja_env: Environment) -> None:
    html = _render(jinja_env, "reset.html")
    assert FAKE_URL in html
    assert html.count(FAKE_URL) >= 2
    assert "{{" not in html
    assert "{%" not in html
    assert "<script" not in html
    assert "Återställ" in html


def test_base_template_has_swedish_lang(jinja_env: Environment) -> None:
    html = _render(jinja_env, "verification.html")
    assert 'lang="sv"' in html


def test_base_has_golfkompis_header(jinja_env: Environment) -> None:
    html = _render(jinja_env, "verification.html")
    assert "Golfkompis" in html


async def test_send_verification_uses_template() -> None:
    mock_fm = MagicMock()
    mock_fm.send_message = AsyncMock()

    with patch("golfkompis.users.email._fm", mock_fm):
        from golfkompis.users.email import send_verification_email

        await send_verification_email("user@example.com", "tok123")

    mock_fm.send_message.assert_called_once()
    call_args = mock_fm.send_message.call_args
    assert call_args.kwargs.get("template_name") == "verification.html"
    msg = call_args.args[0]
    assert msg.template_body is not None
    assert "tok123" in msg.template_body["url"]


async def test_send_reset_uses_template() -> None:
    mock_fm = MagicMock()
    mock_fm.send_message = AsyncMock()

    with patch("golfkompis.users.email._fm", mock_fm):
        from golfkompis.users.email import send_reset_email

        await send_reset_email("user@example.com", "resettok")

    mock_fm.send_message.assert_called_once()
    call_args = mock_fm.send_message.call_args
    assert call_args.kwargs.get("template_name") == "reset.html"
    msg = call_args.args[0]
    assert "resettok" in msg.template_body["url"]
