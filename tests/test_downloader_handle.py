"""DownloaderHandle's pause/resume/stop state machine crosses an asyncio task and a
worker thread; a mistake there deadlocks the bot (e.g. a paused worker that never
wakes for cancellation). These tests attach a fake, yt-dlp-free worker that calls
progress_hook in a loop, so the state machine is verified without any network access
or real downloads. Every blocking wait uses a timeout so a deadlock fails the test
instead of hanging the suite.
"""

import asyncio
import time
from pathlib import Path

import pytest
from yt_dlp.utils import DownloadCancelled

from shorty_bot.downloader.base import DownloaderHandle
from shorty_bot.downloader.models import DownloadResult

TIMEOUT = 2.0
TOTAL_BYTES = 1_000
STEP_DELAY = 0.005


def _fake_worker(
    handle: DownloaderHandle, *, steps: int = 40, delay: float = STEP_DELAY
) -> DownloadResult:
    for i in range(steps):
        handle.progress_hook(
            {
                "status": "downloading",
                "downloaded_bytes": i,
                "total_bytes": TOTAL_BYTES,
            }
        )
        time.sleep(delay)
    return DownloadResult(path=Path("fake.mp4"), width=None, height=None, duration=None, title=None)


def _spawn(
    handle: DownloaderHandle, *, steps: int = 40, delay: float = STEP_DELAY
) -> "asyncio.Task[DownloadResult]":
    task: asyncio.Task[DownloadResult] = asyncio.ensure_future(
        asyncio.to_thread(_fake_worker, handle, steps=steps, delay=delay)
    )
    handle.attach(task)
    return task


async def test_stop_ends_worker_and_result_raises() -> None:
    handle = DownloaderHandle()
    _spawn(handle)
    await asyncio.sleep(0.02)

    assert await handle.stop() is True
    with pytest.raises(DownloadCancelled):
        await asyncio.wait_for(handle.result(), timeout=TIMEOUT)


async def test_stop_while_paused_does_not_deadlock() -> None:
    handle = DownloaderHandle()
    _spawn(handle)
    await asyncio.sleep(0.02)

    assert await handle.pause() is True
    await asyncio.sleep(0.02)  # let the worker thread actually block on the hook

    assert await handle.stop() is True
    with pytest.raises(DownloadCancelled):
        await asyncio.wait_for(handle.result(), timeout=TIMEOUT)


async def test_pause_and_resume_return_values_match_state() -> None:
    handle = DownloaderHandle()
    task = _spawn(handle)
    await asyncio.sleep(0.02)

    assert await handle.pause() is True
    assert await handle.pause() is False  # already paused

    assert await handle.resume() is True
    assert await handle.resume() is False  # not paused

    assert await handle.stop() is True
    await asyncio.wait_for(asyncio.gather(task, return_exceptions=True), timeout=TIMEOUT)


async def test_stop_after_completion_returns_false() -> None:
    handle = DownloaderHandle()
    _spawn(handle, steps=2, delay=0.0)

    result = await asyncio.wait_for(handle.result(), timeout=TIMEOUT)
    assert isinstance(result, DownloadResult)
    assert await handle.stop() is False


async def test_pause_and_resume_return_false_after_completion() -> None:
    handle = DownloaderHandle()
    _spawn(handle, steps=2, delay=0.0)

    await asyncio.wait_for(handle.result(), timeout=TIMEOUT)
    assert await handle.pause() is False
    assert await handle.resume() is False


async def test_progress_reflects_hook_data() -> None:
    handle = DownloaderHandle()
    task = _spawn(handle)
    await asyncio.sleep(0.02)

    assert handle.progress is not None
    assert handle.progress.status == "downloading"
    assert handle.progress.total_bytes == TOTAL_BYTES

    assert await handle.stop() is True
    await asyncio.wait_for(asyncio.gather(task, return_exceptions=True), timeout=TIMEOUT)
