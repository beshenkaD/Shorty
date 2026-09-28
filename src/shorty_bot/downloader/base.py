import asyncio
import re
import threading
from abc import ABC
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, ClassVar

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadCancelled, DownloadError

from shorty_bot.downloader.models import (
    DownloadCancelledError,
    DownloadFailedError,
    DownloadProgress,
    DownloadResult,
    FileTooLargeError,
    MediaKind,
)


class DownloaderHandle:
    """Tracks and controls a single in-flight download.

    yt-dlp-agnostic by design: it only knows about threading.Event and the
    progress dict shape, so it can be exercised in tests with a fake worker
    instead of a real yt-dlp download.

    Limitation: pause() and stop() only take effect the next time yt-dlp
    calls the progress hook (i.e. per downloaded chunk or fragment), not
    immediately.
    """

    def __init__(self) -> None:
        self._cancel_event = threading.Event()
        self._running_event = threading.Event()
        self._running_event.set()
        self.progress: DownloadProgress | None = None
        self._task: asyncio.Task[DownloadResult] | None = None

    def attach(self, task: asyncio.Task[DownloadResult]) -> None:
        self._task = task

    def progress_hook(self, d: dict[str, Any]) -> None:
        """Called by yt-dlp from the worker thread on every progress update."""
        total = d.get("total_bytes") or d.get("total_bytes_estimate")
        # Plain attribute assignment is safe to read from the event loop thread under the GIL.
        self.progress = DownloadProgress(
            status=d.get("status", ""),
            downloaded_bytes=d.get("downloaded_bytes") or 0,
            total_bytes=total,
        )
        self._running_event.wait()
        if self._cancel_event.is_set():
            raise DownloadCancelled

    async def stop(self) -> bool:
        assert self._task is not None, "no worker task attached"
        if self._task.done():
            return False
        self._cancel_event.set()
        # Wake a paused worker so it observes the cancellation instead of blocking forever.
        self._running_event.set()
        return True

    async def pause(self) -> bool:
        assert self._task is not None, "no worker task attached"
        if self._task.done() or not self._running_event.is_set():
            return False
        self._running_event.clear()
        return True

    async def resume(self) -> bool:
        assert self._task is not None, "no worker task attached"
        if self._task.done() or self._running_event.is_set():
            return False
        self._running_event.set()
        return True

    async def result(self) -> DownloadResult:
        assert self._task is not None, "no worker task attached"
        return await self._task


class BaseDownloader(ABC):
    """Owns the shared yt-dlp machinery. Subclasses set `url_pattern`."""

    url_pattern: ClassVar[re.Pattern[str]]

    def __init__(self, *, max_bytes: int, semaphore: asyncio.Semaphore) -> None:
        self._max_bytes = max_bytes
        self._semaphore = semaphore

    def match(self, text: str) -> str | None:
        m = self.url_pattern.search(text)
        return m.group(0) if m else None

    def _format_selector(self, media: MediaKind) -> str:
        size_filter = f"[filesize<?{self._max_bytes}]"
        if media is MediaKind.VIDEO:
            return f"bv*{size_filter}"
        if media is MediaKind.AUDIO:
            return f"ba{size_filter}"
        return f"bv*{size_filter}+ba{size_filter}/b{size_filter}"

    def _ydl_opts(self, destination: Path, media: MediaKind) -> dict[str, Any]:
        return {
            "outtmpl": str(destination / "%(id)s.%(ext)s"),
            "max_filesize": self._max_bytes,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "format": self._format_selector(media),
        }

    @asynccontextmanager
    async def download(
        self, link: str, destination: Path, media: MediaKind = MediaKind.BOTH
    ) -> AsyncIterator[DownloaderHandle]:
        async with self._semaphore:
            handle = DownloaderHandle()
            task = asyncio.ensure_future(
                asyncio.to_thread(self._run, link, destination, media, handle)
            )
            handle.attach(task)
            try:
                yield handle
            finally:
                if not task.done():
                    await handle.stop()
                # Always await so the worker thread is never leaked, even on cancellation.
                await asyncio.gather(task, return_exceptions=True)

    def _run(
        self, link: str, destination: Path, media: MediaKind, handle: DownloaderHandle
    ) -> DownloadResult:
        opts = self._ydl_opts(destination, media)
        opts["progress_hooks"] = [handle.progress_hook]
        try:
            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(link, download=True)
        except DownloadCancelled as exc:
            raise DownloadCancelledError(str(exc)) from exc
        except DownloadError as exc:
            raise DownloadFailedError(str(exc)) from exc

        assert info is not None, "extract_info returned no info without raising"
        downloaded = info["requested_downloads"][0]
        # yt-dlp aborts a format over `max_filesize` without raising, leaving no filepath.
        if "filepath" not in downloaded:
            raise FileTooLargeError(f"yt-dlp skipped a file over the {self._max_bytes} byte limit")
        path = Path(downloaded["filepath"])

        size = path.stat().st_size
        if size > self._max_bytes:
            # The downloader never deletes files; the caller owns `destination`.
            raise FileTooLargeError(f"downloaded file is {size} bytes, limit is {self._max_bytes}")

        duration = info.get("duration")
        return DownloadResult(
            path=path,
            width=downloaded.get("width"),
            height=downloaded.get("height"),
            duration=int(duration) if duration is not None else None,
            title=info.get("title"),
        )
