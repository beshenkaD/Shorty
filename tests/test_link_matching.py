"""Which links get accepted is the core routing rule of the bot: a false negative
means a valid Shorts/TikTok link silently gets ignored, and a false positive means
we try to feed yt-dlp a URL it can't handle. These tests pin that behavior without
touching the network.
"""

import asyncio

from shorty_bot.downloader import DownloaderRegistry
from shorty_bot.downloader.tiktok import TikTokDownloader
from shorty_bot.downloader.yt import YouTubeDownloader

MAX_BYTES = 50_000_000


def _make_yt() -> YouTubeDownloader:
    return YouTubeDownloader(max_bytes=MAX_BYTES, semaphore=asyncio.Semaphore(1))


def _make_tiktok() -> TikTokDownloader:
    return TikTokDownloader(max_bytes=MAX_BYTES, semaphore=asyncio.Semaphore(1))


class TestYouTubeMatch:
    def test_accepts_shorts_with_scheme(self) -> None:
        assert _make_yt().match("https://www.youtube.com/shorts/abc123XYZ") is not None

    def test_accepts_shorts_without_scheme(self) -> None:
        assert _make_yt().match("youtube.com/shorts/abc123XYZ") is not None

    def test_accepts_m_subdomain(self) -> None:
        assert _make_yt().match("https://m.youtube.com/shorts/abc123XYZ") is not None

    def test_accepts_with_query_string(self) -> None:
        url = "https://youtube.com/shorts/abc123XYZ?feature=share"
        assert _make_yt().match(url) is not None

    def test_accepts_link_embedded_in_text(self) -> None:
        url = "https://youtube.com/shorts/abc123XYZ"
        found = _make_yt().match(f"check this out {url} nice right?")
        assert found == url

    def test_rejects_watch_url(self) -> None:
        assert _make_yt().match("https://www.youtube.com/watch?v=abc123XYZ") is None

    def test_rejects_youtu_be(self) -> None:
        assert _make_yt().match("https://youtu.be/abc123XYZ") is None

    def test_rejects_lookalike_domain(self) -> None:
        yt = _make_yt()
        assert yt.match("https://fakeyoutube.com/shorts/abc123XYZ") is None
        assert yt.match("https://notyoutube.com.evil.com/shorts/abc123XYZ") is None


class TestTikTokMatch:
    def test_accepts_full_link(self) -> None:
        url = "https://www.tiktok.com/@someuser/video/7123456789012345678"
        assert _make_tiktok().match(url) is not None

    def test_accepts_vm_short_link(self) -> None:
        assert _make_tiktok().match("https://vm.tiktok.com/ZMecpQFeR/") is not None

    def test_accepts_vt_short_link(self) -> None:
        assert _make_tiktok().match("https://vt.tiktok.com/ZSabcdefg/") is not None

    def test_accepts_t_redirect_link(self) -> None:
        assert _make_tiktok().match("https://www.tiktok.com/t/ZTabcdefg/") is not None

    def test_rejects_lookalike_domain(self) -> None:
        url = "https://faketiktok.com/@someuser/video/123"
        assert _make_tiktok().match(url) is None

    def test_rejects_unrelated_url(self) -> None:
        url = "https://example.com/@someuser/video/123"
        assert _make_tiktok().match(url) is None


class TestDownloaderRegistryFind:
    def _registry(self) -> DownloaderRegistry:
        return DownloaderRegistry.default(max_bytes=MAX_BYTES, max_concurrent=2)

    def test_routes_youtube_shorts_to_youtube_downloader(self) -> None:
        url = "https://www.youtube.com/shorts/abc123XYZ"
        found = self._registry().find(url)
        assert found is not None
        downloader, matched_url = found
        assert isinstance(downloader, YouTubeDownloader)
        assert matched_url == url

    def test_routes_tiktok_to_tiktok_downloader(self) -> None:
        found = self._registry().find("https://vm.tiktok.com/ZMecpQFeR/")
        assert found is not None
        downloader, _ = found
        assert isinstance(downloader, TikTokDownloader)

    def test_returns_none_for_unrelated_text(self) -> None:
        assert self._registry().find("just a regular message with no links") is None
