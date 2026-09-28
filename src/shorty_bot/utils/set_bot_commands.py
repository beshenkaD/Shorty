from aiogram import Bot
from aiogram.types import BotCommand


async def set_bot_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Show the welcome message"),
            BotCommand(command="help", description="List supported links"),
        ]
    )
