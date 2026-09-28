from aiogram import Router

from shorty_bot.handlers import errors, users

router = Router(name="root")
router.include_router(users.router)
router.include_router(errors.router)

__all__ = ["router"]
