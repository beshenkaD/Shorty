import logging

from aiogram import Router
from aiogram.types import ErrorEvent

logger = logging.getLogger(__name__)

router = Router(name="errors")


@router.errors()
async def error_handler(event: ErrorEvent) -> None:
    logger.exception("Unhandled exception while processing update", exc_info=event.exception)
