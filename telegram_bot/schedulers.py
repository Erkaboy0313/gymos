from apscheduler.schedulers.asyncio import AsyncIOScheduler
from subscriptions.services import send_member_expiry_alerts
from asgiref.sync import sync_to_async
import asyncio
import time
from aiogram.exceptions import TelegramRetryAfter
from django.conf import settings


def setup_scheduler(bot):
    scheduler = AsyncIOScheduler(timezone=str(getattr(settings, "TIME_ZONE", "UTC")))
    loop = asyncio.get_running_loop()

    def send_sync(chat_id: int, text: str, log):
        try:
            asyncio.run_coroutine_threadsafe(bot.send_message(chat_id=chat_id, text=text), loop)
            log.send = True
            log.save()
            return True
        except TelegramRetryAfter as e:
            time.sleep(e.retry_after + 1)
            return send_sync(chat_id,text)
        except Exception as e:
            log.reason = f"{e}"
            log.save()
            return False

    async def job():
        await sync_to_async(send_member_expiry_alerts, thread_sensitive=True)(send_sync)

    # scheduler.add_job(job, CronTrigger(hour=9, minute=0))
    scheduler.add_job(job, "interval", minutes=1)
    
    scheduler.start()
    
    return scheduler



