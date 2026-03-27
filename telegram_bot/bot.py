import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

from django.conf import settings
from telegram_bot.handlers import on_start, on_contact, on_my_qr  # adjust if needed
from .schedulers import setup_scheduler

def setup_routes(dp: Dispatcher):
    dp.message.register(on_start, CommandStart())
    dp.message.register(on_contact, lambda m: m.contact is not None)
    dp.message.register(on_my_qr, lambda m: (m.text or "").strip() == "🧾 My QR")


async def main():
    logging.basicConfig(level=logging.INFO)

    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()
    setup_routes(dp)
    setup_scheduler(bot)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())