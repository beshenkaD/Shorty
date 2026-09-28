import re
from pathlib import Path
from typing import Any, ClassVar

from shorty_bot.downloader.base import BaseDownloader
from shorty_bot.downloader.models import MediaKind


class YouTubeDownloader(BaseDownloader):
    # Shorts only. `(?<![\w.-])` stops "fakeyoutube.com/shorts/x" from matching by
    # requiring the domain to start at a URL/word boundary rather than mid-string.
    url_pattern: ClassVar[re.Pattern[str]] = re.compile(
        r"(?<![\w.-])(?:https?://)?(?:www\.|m\.)?youtube\.com/shorts/[\w-]+(?:\?\S*)?"
    )

    def _format_selector(self, media: MediaKind) -> str:
        size_filter = f"[filesize<?{self._max_bytes}]"
        # Prefer mp4/m4a, but fall back to any container rather than failing outright.
        fallback = super()._format_selector(media)
        if media is MediaKind.VIDEO:
            return f"bv*[ext=mp4]{size_filter}/{fallback}"
        if media is MediaKind.AUDIO:
            return f"ba[ext=m4a]{size_filter}/{fallback}"
        return (
            f"bv*[ext=mp4]{size_filter}+ba[ext=m4a]{size_filter}/b[ext=mp4]{size_filter}/{fallback}"
        )

    def _ydl_opts(self, destination: Path, media: MediaKind) -> dict[str, Any]:
        opts = super()._ydl_opts(destination, media)
        # YouTube serves audio/video as separate streams; ffmpeg merges them into mp4.
        opts["merge_output_format"] = "mp4"
        return opts
