import re
from pathlib import Path
from typing import Any, ClassVar

from shorty_bot.downloader.base import BaseDownloader
from shorty_bot.downloader.models import MediaKind


class InstagramDownloader(BaseDownloader):
    # Reels only: /reel/, /reels/, /<user>/reel/, and /share/reel/ links (yt-dlp follows
    # the share redirect to the canonical reel). `(?<![\w.-])` stops "fakeinstagram.com"
    # from matching by requiring the domain to start at a URL/word boundary.
    url_pattern: ClassVar[re.Pattern[str]] = re.compile(
        r"(?<![\w.-])(?:https?://)?(?:www\.)?instagram\.com/(?:share/)?"
        r"(?:[\w.]+/)?reels?/[\w-]+/?(?:\?\S*)?"
    )

    def _format_selector(self, media: MediaKind) -> str:
        size_filter = f"[filesize<?{self._max_bytes}]"
        fallback = super()._format_selector(media)
        if media is MediaKind.VIDEO:
            return f"bv*[ext=mp4]{size_filter}/{fallback}"
        if media is MediaKind.AUDIO:
            return f"ba[ext=m4a]{size_filter}/{fallback}"
        # Instagram serves pre-muxed progressive mp4s; prefer them over the DASH
        # bv+ba fallback to avoid an ffmpeg merge.
        return (
            f"b[ext=mp4]{size_filter}/bv*[ext=mp4]{size_filter}+ba[ext=m4a]{size_filter}/{fallback}"
        )

    def _ydl_opts(self, destination: Path, media: MediaKind) -> dict[str, Any]:
        opts = super()._ydl_opts(destination, media)
        # Needed for the DASH video+audio fallback, which ffmpeg merges into mp4.
        opts["merge_output_format"] = "mp4"
        return opts
