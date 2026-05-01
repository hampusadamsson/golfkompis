"""Unit tests for MinGolf.login() — bad-credentials and error-extraction paths."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from golfkompis.mingolf import (
    InvalidCredentials,
    MinGolf,
    _extract_login_error,  # pyright: ignore[reportPrivateUsage]
)

# ---------------------------------------------------------------------------
# _extract_login_error helpers
# ---------------------------------------------------------------------------


def _mock_response(
    status_code: int, body: object | None = None, text: str = ""
) -> requests.Response:
    r = requests.Response()
    r.status_code = status_code
    if body is not None:
        r._content = json.dumps(body).encode()
        r.headers["Content-Type"] = "application/json"
    else:
        r._content = text.encode()
    return r


def test_extract_login_error_bare_string() -> None:
    r = _mock_response(400, "Du har angivit fel lösenord eller användarnamn.")
    assert _extract_login_error(r) == "Du har angivit fel lösenord eller användarnamn."


def test_extract_login_error_dict_with_message_key() -> None:
    r = _mock_response(400, {"Message": "Some error"})
    assert _extract_login_error(r) == "Some error"


def test_extract_login_error_non_json_fallback() -> None:
    r = _mock_response(400, text="plain text error")
    assert _extract_login_error(r) == "plain text error"


def test_extract_login_error_empty_body() -> None:
    r = _mock_response(400, text="")
    assert _extract_login_error(r) is None


# ---------------------------------------------------------------------------
# MinGolf.login()
# ---------------------------------------------------------------------------


def test_login_400_bare_string_raises_invalid_credentials() -> None:
    msg = "Du har angivit fel lösenord eller användarnamn."
    mock_resp = _mock_response(400, msg)

    with patch("golfkompis.mingolf.requests.Session") as mock_sess_cls:
        mock_sess = MagicMock()
        mock_sess_cls.return_value = mock_sess
        mock_sess.post.return_value = mock_resp
        mock_sess.headers = MagicMock()

        client = MinGolf(session=mock_sess)
        with pytest.raises(InvalidCredentials, match="fel lösenord"):
            client.login("123456-789", "wrongpassword")


def test_login_400_dict_message_raises_invalid_credentials() -> None:
    mock_resp = _mock_response(400, {"Message": "Invalid credentials"})

    with patch("golfkompis.mingolf.requests.Session") as mock_sess_cls:
        mock_sess = MagicMock()
        mock_sess_cls.return_value = mock_sess
        mock_sess.post.return_value = mock_resp
        mock_sess.headers = MagicMock()

        client = MinGolf(session=mock_sess)
        with pytest.raises(InvalidCredentials, match="Invalid credentials"):
            client.login("123456-789", "wrongpassword")


def test_login_500_raises_http_error() -> None:
    mock_resp = requests.Response()
    mock_resp.status_code = 500
    mock_resp._content = b"Internal Server Error"

    with patch("golfkompis.mingolf.requests.Session") as mock_sess_cls:
        mock_sess = MagicMock()
        mock_sess_cls.return_value = mock_sess
        mock_sess.post.return_value = mock_resp
        mock_sess.headers = MagicMock()

        client = MinGolf(session=mock_sess)
        with pytest.raises(requests.HTTPError):
            client.login("123456-789", "pass")


def test_login_200_no_access_token_raises_invalid_credentials() -> None:
    mock_resp = _mock_response(200, {"someOtherField": True})

    with patch("golfkompis.mingolf.requests.Session") as mock_sess_cls:
        mock_sess = MagicMock()
        mock_sess_cls.return_value = mock_sess
        mock_sess.post.return_value = mock_resp
        mock_sess.headers = MagicMock()

        client = MinGolf(session=mock_sess)
        with pytest.raises(InvalidCredentials):
            client.login("123456-789", "pass")


def test_login_success_sets_authenticated() -> None:
    mock_resp = _mock_response(200, {"accessToken": "tok123"})

    with patch("golfkompis.mingolf.requests.Session") as mock_sess_cls:
        mock_sess = MagicMock()
        mock_sess_cls.return_value = mock_sess
        mock_sess.post.return_value = mock_resp
        mock_sess.headers = MagicMock()

        client = MinGolf(session=mock_sess)
        client.login("123456-789", "correctpassword")
        assert client._authenticated is True  # pyright: ignore[reportPrivateUsage]


def test_invalid_credentials_is_subclass_of_value_error() -> None:
    assert issubclass(InvalidCredentials, ValueError)
