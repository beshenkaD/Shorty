from pathlib import Path
from tempfile import TemporaryDirectory

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.types import FSInputFile, Message
from aiogram.utils.chat_action import ChatActionSender

from shorty_bot.downloader import BaseDownloader, DownloaderError, FileTooLargeError
from shorty_bot.filters import VideoLinkFilter
from shorty_bot.handlers.users.help import SUPPORTED_LINKS

router = Router(name="video")

SUPPORTED_LINKS_HINT = "I didn't recognize that link.\n\n" + SUPPORTED_LINKS


@router.message(F.text, VideoLinkFilter())
async def video_handler(message: Message, bot: Bot, downloader: BaseDownloader, url: str) -> None:
    async with ChatActionSender.upload_video(chat_id=message.chat.id, bot=bot):
        with TemporaryDirectory() as tmp_dir:
            try:
                async with downloader.download(url, Path(tmp_dir)) as handle:
                    result = await handle.result()
            except FileTooLargeError:
                await message.reply("This video is too large to send, sorry.")
                return
            except DownloaderError:
                await message.reply("I couldn't download this video, sorry.")
                return

            await message.reply_video(
                FSInputFile(result.path),
                width=result.width,
                height=result.height,
                duration=result.duration,
                supports_streaming=True,
            )


@router.message(F.chat.type == ChatType.PRIVATE, F.text)
async def unsupported_link_handler(message: Message) -> None:
    await message.reply(SUPPORTED_LINKS_HINT)
