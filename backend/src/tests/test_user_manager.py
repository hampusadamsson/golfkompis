"""Unit tests for UserManager event hooks."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from golfkompis.users.manager import UserManager


@pytest.fixture()
def user_manager() -> UserManager:
    return UserManager(user_db=AsyncMock())  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_on_after_register_calls_request_verify(
    user_manager: UserManager,
) -> None:
    user = AsyncMock()
    user.email = "test@example.com"
    user_manager.request_verify = AsyncMock()  # type: ignore[method-assign]

    await user_manager.on_after_register(user)

    user_manager.request_verify.assert_awaited_once_with(user, None)


@pytest.mark.asyncio
async def test_on_after_forgot_password_calls_send_reset_email(
    user_manager: UserManager,
) -> None:
    user = AsyncMock()
    user.email = "test@example.com"

    with patch(
        "golfkompis.users.email.send_reset_email", new_callable=AsyncMock
    ) as mock_email:
        await user_manager.on_after_forgot_password(user, "tok456")
        mock_email.assert_awaited_once_with("test@example.com", "tok456")


@pytest.mark.asyncio
async def test_on_after_request_verify_calls_send_verification_email(
    user_manager: UserManager,
) -> None:
    user = AsyncMock()
    user.email = "test@example.com"

    with patch(
        "golfkompis.users.email.send_verification_email", new_callable=AsyncMock
    ) as mock_email:
        await user_manager.on_after_request_verify(user, "verif_tok")
        mock_email.assert_awaited_once_with("test@example.com", "verif_tok")
