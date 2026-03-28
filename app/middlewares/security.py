from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, Update, User

from app.core import config

audit = logging.getLogger("audit")

IGNORED_FIELDS = {"update_id"}


def _format_user(user: User | None) -> str:
    if user is None:
        return "unknown"
    parts = [f"id={user.id}"]
    if user.username:
        parts.append(f"@{user.username}")
    parts.append(user.full_name)
    return " ".join(parts)


def _describe_message(msg: Message) -> str:
    if msg.video:
        return "message:video"
    if msg.text and msg.text.startswith("/"):
        return f"message:command({msg.text.split()[0]})"
    return "message:other"


def _detect_event(update: Update) -> tuple[str, User | None, Message | CallbackQuery | None]:
    """Return (event_name, from_user, actionable_object) for any Update."""
    if update.message is not None:
        return _describe_message(update.message), update.message.from_user, update.message

    if update.callback_query is not None:
        cq = update.callback_query
        return f"callback_query({cq.data})", cq.from_user, cq

    filled = update.model_fields_set - IGNORED_FIELDS
    event_name = next(iter(filled), "unknown")

    obj = getattr(update, event_name, None) if event_name != "unknown" else None
    user = None
    if obj is not None:
        user = getattr(obj, "from_user", None) or getattr(obj, "user", None)

    return event_name, user, None


class SecurityMiddleware(BaseMiddleware):
    """
    Single dp.update middleware: logging + whitelist + event filtering.

    For message/callback_query:
      - log the event
      - check whitelist, block with a reply if denied
    For everything else:
      - log and drop (we don't process these event types)
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        assert isinstance(event, Update), (
            f"SecurityMiddleware must be registered on dp.update, got {type(event).__name__}"
        )

        event_name, user, inner = _detect_event(event)
        user_str = _format_user(user)

        if inner is None:
            audit.info("[ignored] %s from %s", event_name, user_str)
            return

        audit.info("[event] %s from %s", event_name, user_str)

        user_id = user.id if user else None
        if config.is_user_allowed(user_id):
            return await handler(event, data)

        audit.warning("[blocked] %s from %s — not in whitelist", event_name, user_str)

        i18n = data.get("i18n")
        text = i18n.get("access-denied-text")

        if isinstance(inner, CallbackQuery):
            await inner.answer(text, show_alert=True)
            return

        if isinstance(inner, Message):
            try:
                await inner.delete()
            except Exception:
                pass
            await inner.answer(text)
            return
