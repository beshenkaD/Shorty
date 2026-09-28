from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router(name="start")


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer(
        "Hi! Send me a YouTube Shorts or TikTok link and I'll send the video back."
    )
