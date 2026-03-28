import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from aiogram_i18n import I18nMiddleware
from aiogram_i18n.cores.fluent_runtime_core import FluentRuntimeCore

from app.commands import start_router, help_router
from app.core import logger, setup_logging, config
from app.handlers import video_router
from app.middlewares import SecurityMiddleware


async def _resolve_channel_label(bot: Bot) -> str:
    try:
        chat = await bot.get_chat(config.CHANNEL_ID)
        if chat.username:
            return f"@{chat.username}"
        if chat.title:
            return chat.title
    except Exception as e:
        logger.warning(f"Failed to resolve channel label for {config.CHANNEL_ID}: {e}")
    return str(config.CHANNEL_ID)


async def main() -> None:
    setup_logging()

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            link_preview_is_disabled=True
        )
    )

    commands = [
        BotCommand(command="start", description="🚀 Start the app"),
        BotCommand(command="help", description="📖 Show help information")
    ]
    await bot.set_my_commands(commands)
    config.set_channel_label(await _resolve_channel_label(bot))
    logger.info(f"Resolved channel label: {config.CHANNEL_LABEL}")

    i18n_core = FluentRuntimeCore(path="locales/{locale}")
    await i18n_core.startup()
    logger.info(f"Loaded locales: {i18n_core.available_locales}")
    i18n = I18nMiddleware(core=i18n_core, default_locale="ru")

    dp = Dispatcher()

    for router in [start_router, help_router, video_router]:
        dp.include_router(router)

    i18n.setup(dispatcher=dp)
    dp.update.outer_middleware(SecurityMiddleware())

    try:
        await dp.start_polling(
            bot,
            allowed_updates=["message", "callback_query"],
            polling_timeout=30,
            handle_as_tasks=True,
            tasks_concurrency_limit=100,
            close_bot_session=True,
        )
    finally:
        await i18n.core.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
