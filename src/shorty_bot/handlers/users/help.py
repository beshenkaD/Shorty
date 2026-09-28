from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="help")

SUPPORTED_LINKS = (
    "Supported links:\n"
    "- YouTube Shorts: youtube.com/shorts/&lt;id&gt;\n"
    "- TikTok: tiktok.com/@user/video/&lt;id&gt;, vm.tiktok.com/&lt;code&gt;, "
    "vt.tiktok.com/&lt;code&gt;\n"
    "- Instagram Reels: instagram.com/reel/&lt;id&gt;"
)


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    await message.answer(
        "Send a YouTube Shorts, TikTok or Instagram Reels link and I'll download and "
        "send the video back.\n\n" + SUPPORTED_LINKS
    )
