"""fastapi-users manager, auth backend, and dependency helpers."""

import uuid
from collections.abc import AsyncGenerator

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import AuthenticationBackend, CookieTransport
from fastapi_users.authentication.strategy.db import DatabaseStrategy
from fastapi_users.db import SQLAlchemyUserDatabase

from golfkompis.config import settings
from golfkompis.users.db import (
    get_access_token_db,  # pyright: ignore[reportUnknownVariableType]
    get_user_db,  # pyright: ignore[reportUnknownVariableType]
)
from golfkompis.users.models import User

# ---------------------------------------------------------------------------
# Transport + strategy
# ---------------------------------------------------------------------------

_cookie_transport = CookieTransport(
    cookie_max_age=settings.auth_cookie_lifetime_seconds,
    cookie_secure=settings.auth_cookie_secure,
)


def _get_database_strategy(  # pyright: ignore[reportUnknownParameterType]
    access_token_db: SQLAlchemyUserDatabase = Depends(get_access_token_db),  # type: ignore[type-arg]  # pyright: ignore[reportUnknownVariableType,reportUnknownArgumentType]
) -> DatabaseStrategy:  # type: ignore[type-arg]
    return DatabaseStrategy(  # type: ignore[return-value]
        access_token_db,  # type: ignore[arg-type]
        lifetime_seconds=settings.auth_cookie_lifetime_seconds,
    )


auth_backend: AuthenticationBackend = AuthenticationBackend(  # type: ignore[type-arg]
    name="cookie",
    transport=_cookie_transport,
    get_strategy=_get_database_strategy,  # pyright: ignore[reportUnknownArgumentType]
)

# ---------------------------------------------------------------------------
# User manager
# ---------------------------------------------------------------------------


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = settings.auth_secret
    verification_token_secret = settings.auth_secret

    async def on_after_register(
        self, user: User, request: Request | None = None
    ) -> None:
        await self.request_verify(user, request)

    async def on_after_forgot_password(
        self, user: User, token: str, request: Request | None = None
    ) -> None:
        from golfkompis.users.email import send_reset_email

        await send_reset_email(user.email, token)

    async def on_after_request_verify(
        self, user: User, token: str, request: Request | None = None
    ) -> None:
        from golfkompis.users.email import send_verification_email

        await send_verification_email(user.email, token)


async def get_user_manager(
    user_db: SQLAlchemyUserDatabase = Depends(get_user_db),  # type: ignore[type-arg]  # pyright: ignore[reportUnknownVariableType,reportUnknownParameterType]
) -> AsyncGenerator[UserManager]:
    yield UserManager(user_db)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# FastAPIUsers instance + convenience dependency
# ---------------------------------------------------------------------------

fastapi_users: FastAPIUsers[User, uuid.UUID] = FastAPIUsers[User, uuid.UUID](
    get_user_manager,  # type: ignore[arg-type]
    [auth_backend],  # pyright: ignore[reportUnknownArgumentType]
)

current_active_user = fastapi_users.current_user(active=True)
