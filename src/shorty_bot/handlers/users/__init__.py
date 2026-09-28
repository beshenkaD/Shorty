from aiogram import Router

from shorty_bot.handlers.users import help as help_module
from shorty_bot.handlers.users import start, video

router = Router(name="users")
router.include_router(start.router)
router.include_router(help_module.router)
router.include_router(video.router)

__all__ = ["router"]
