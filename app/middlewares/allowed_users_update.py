from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from app.core import config


class AllowedUsersUpdateMiddleware(BaseMiddleware):
    """
    Strict guard for non-message updates.

    We intentionally allow Message/CallbackQuery updates to pass through here
    because they are handled by per-event middleware that can reply to the user.
    For other update types we just stop processing for all types of users.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Let message/callback updates pass, they will be handled (and replied to)
        # by AllowedUsersMiddleware on dp.message / dp.callback_query.
        if event.message is not None or event.callback_query is not None:
            return await handler(event, data)

        return
