from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from shorty_bot import handlers
from shorty_bot.data.config import Settings
from shorty_bot.downloader import DownloaderRegistry


def create_bot(settings: Settings) -> Bot:
    return Bot(
        token=settings.telegram_bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher(registry: DownloaderRegistry) -> Dispatcher:
    dispatcher = Dispatcher(downloaders=registry)
    dispatcher.include_router(handlers.router)
    return dispatcher
