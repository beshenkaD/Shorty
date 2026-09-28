from typing import Any

from aiogram.filters import Filter
from aiogram.types import Message

from shorty_bot.downloader import DownloaderRegistry


class VideoLinkFilter(Filter):
    """Matches a message containing a supported video link.

    Resolves the matching downloader and canonical URL, passing them to the
    handler as `downloader` and `url` via the dict-merge filter contract.
    """

    async def __call__(
        self, message: Message, downloaders: DownloaderRegistry
    ) -> dict[str, Any] | bool:
        if message.text is None:
            return False
        found = downloaders.find(message.text)
        if found is None:
            return False
        downloader, url = found
        return {"downloader": downloader, "url": url}
