import re
from typing import ClassVar

from shorty_bot.downloader.base import BaseDownloader


class TikTokDownloader(BaseDownloader):
    """
    Later: authorization, tt specific features
    """

    # Full links (tiktok.com/@user/video/<id>), the /t/<code> redirect form, and the
    # vm./vt. short-link domains. `(?<![\w.-])` blocks look-alike domains such as
    # "faketiktok.com" by requiring the match to start at a URL/word boundary.
    url_pattern: ClassVar[re.Pattern[str]] = re.compile(
        r"(?<![\w.-])(?:https?://)?"
        r"(?:"
        r"(?:www\.)?tiktok\.com/@[\w.-]+/video/\d+"
        r"|(?:www\.)?tiktok\.com/t/[\w-]+"
        r"|v[mt]\.tiktok\.com/[\w-]+"
        r")/?(?:\?\S*)?"
    )
