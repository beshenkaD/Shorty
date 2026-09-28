from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path


class MediaKind(Enum):
    VIDEO = auto()
    AUDIO = auto()
    BOTH = auto()


@dataclass(slots=True)
class DownloadProgress:
    status: str
    downloaded_bytes: int
    total_bytes: int | None

    @property
    def fraction(self) -> float | None:
        if not self.total_bytes:
            return None
        return self.downloaded_bytes / self.total_bytes


@dataclass(slots=True)
class DownloadResult:
    path: Path
    width: int | None
    height: int | None
    duration: int | None
    title: str | None


class DownloaderError(Exception):
    """Base class for all downloader errors. The bot layer never imports yt-dlp."""


class DownloadFailedError(DownloaderError):
    """yt-dlp raised a DownloadError during extraction or download."""


class DownloadCancelledError(DownloaderError):
    """The download was cancelled via DownloaderHandle.stop()."""


class FileTooLargeError(DownloaderError):
    """The downloaded file exceeds the configured size limit."""
