from __future__ import annotations

import logging

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.core import config

logger = logging.getLogger(__name__)


class AllowedUsersMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:

        user_id = getattr(getattr(event, "from_user", None), "id", None)
        if config.is_user_allowed(user_id):
            return await handler(event, data)

        i18n = data.get("i18n")
        text = i18n.get("access-denied-text")

        if isinstance(event, CallbackQuery):
            try:
                await event.answer(text, show_alert=True)
            finally:
                return

        if isinstance(event, Message):
            try:
                await event.delete()
            except Exception:
                pass
            await event.answer(text)
            return

        return

