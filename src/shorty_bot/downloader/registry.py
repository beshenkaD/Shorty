import asyncio
from dataclasses import dataclass

from shorty_bot.downloader.base import BaseDownloader
from shorty_bot.downloader.tiktok import TikTokDownloader
from shorty_bot.downloader.yt import YouTubeDownloader


@dataclass
class DownloaderRegistry:
    downloaders: tuple[BaseDownloader, ...]

    def find(self, text: str) -> tuple[BaseDownloader, str] | None:
        for downloader in self.downloaders:
            url = downloader.match(text)
            if url is not None:
                return downloader, url
        return None

    @classmethod
    def default(cls, *, max_bytes: int, max_concurrent: int) -> "DownloaderRegistry":
        # Shared semaphore: caps *total* concurrent downloads across all platforms.
        semaphore = asyncio.Semaphore(max_concurrent)
        return cls(
            downloaders=(
                YouTubeDownloader(max_bytes=max_bytes, semaphore=semaphore),
                TikTokDownloader(max_bytes=max_bytes, semaphore=semaphore),
            )
        )
