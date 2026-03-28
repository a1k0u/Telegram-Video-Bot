import logging

from aiogram import Bot, Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, ReplyParameters
from aiogram_i18n import I18nContext

from app.core import config
from app.utils import process_video

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.message(F.video)
async def video_handler(message: Message, i18n: I18nContext, bot: Bot) -> None:
    await process_video(message, i18n, bot)


@router.callback_query(F.data.startswith("post_circle:"))
async def post_circle_to_channel(callback: CallbackQuery, i18n: I18nContext, bot: Bot) -> None:
    if not callback.message:
        await callback.answer()
        return

    _, _, raw_message_id = callback.data.partition(":")
    try:
        message_id = int(raw_message_id)
    except ValueError:
        await callback.answer(i18n.get("post-to-channel-failed-text", error="Invalid message id"), show_alert=True)
        return

    from_chat_id = callback.message.chat.id

    try:
        await bot.copy_message(
            chat_id=config.CHANNEL_ID,
            from_chat_id=from_chat_id,
            message_id=message_id,
        )
        await bot.edit_message_reply_markup(chat_id=from_chat_id, message_id=message_id, reply_markup=None)
        await callback.answer(i18n.get("posted-to-channel-text"))
        try:
            await bot.send_message(
                chat_id=from_chat_id,
                text=i18n.get("posted-to-channel-text"),
                reply_parameters=ReplyParameters(message_id=message_id),
            )
        except Exception as e:
            logger.warning(f"Failed to send post log message: {e}")
    except Exception as e:
        logger.warning(f"Failed to post circle to channel {config.CHANNEL_ID}: {e}")
        await callback.answer(i18n.get("post-to-channel-failed-text", error=str(e)), show_alert=True)


@router.message(~F.video & ~(F.text.regexp(r"^/(start|help)(?:@\\w+)?(?:\\s|$)")))
async def handle_unknown_input(message: Message, i18n: I18nContext) -> None:
    await message.delete()
    await message.answer(i18n.get("unknown-input-text"))
