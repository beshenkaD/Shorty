import asyncio
import logging

from shorty_bot.data.config import Settings
from shorty_bot.downloader import DownloaderRegistry
from shorty_bot.loader import create_bot, create_dispatcher
from shorty_bot.utils import set_bot_commands


async def _run() -> None:
    settings = Settings()
    registry = DownloaderRegistry.default(
        max_bytes=settings.max_file_size_mb * 1024 * 1024,
        max_concurrent=settings.max_concurrent_downloads,
    )
    bot = create_bot(settings)
    dispatcher = create_dispatcher(registry)

    await set_bot_commands(bot)
    await dispatcher.start_polling(bot, allowed_updates=dispatcher.resolve_used_update_types())


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_run())
