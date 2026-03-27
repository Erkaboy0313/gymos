from django.core.management.base import BaseCommand
from telegram_bot.bot import main
import asyncio


class Command(BaseCommand):
    help = "Run Telegram bot (aiogram polling)"

    def handle(self, *args, **options):
        asyncio.run(main())