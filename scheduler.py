# scheduler.py
import logging
from datetime import time
import os
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

from storage import get_all_users_with_settings, get_user_setting, get_random_question
from state import user_state  # общий словарь

load_dotenv()
TZ = os.getenv("TZ")
logging.basicConfig(level=logging.INFO)
scheduler = AsyncIOScheduler(timezone=TZ)
bot: Bot | None = None

TIME_SLOTS = [time(19, 0), time(16, 0), time(12, 0)]

def _job_id(user_id: int, slot: int) -> str:
    return f"user:{user_id}:slot:{slot}"

async def send_daily_question(user_id: int):
    q = await get_random_question()
    if q and bot:
        try:
            # сохраняем состояние, чтобы следующий ответ привязался к вопросу
            user_state[user_id] = q.id
            await bot.send_message(chat_id=user_id, text=f"👀 {q.text}")
        except Exception as e:
            logging.warning(f"Не удалось отправить сообщение {user_id}: {e}")
            


def remove_user_jobs(user_id: int):
    """Удалить все существующие джобы пользователя (по нашим слотам)."""
    for i in range(len(TIME_SLOTS)):
        jid = _job_id(user_id, i)
        if scheduler.get_job(jid):
            scheduler.remove_job(jid)
            logging.info(f"Удалена джоба {jid} для пользователя {user_id}")

def schedule_user(user_id: int, times: int):
    """Создать/обновить джобы для пользователя под нужное кол-во слотов."""
    remove_user_jobs(user_id)
    for i in range(min(times, len(TIME_SLOTS))):
        t = TIME_SLOTS[i]
        jid = _job_id(user_id, i)
        scheduler.add_job(
            send_daily_question,
            trigger=CronTrigger(hour=t.hour, minute=t.minute),
            args=[user_id],
            id=jid,
            replace_existing=True,
        )
        logging.info(f"Создана джоба {jid} для пользователя {user_id} на {t.hour}:{t.minute:02d}")

async def refresh_user_jobs(user_id: int):
    """Прочитать настройку из БД и пересоздать джобы для конкретного пользователя."""
    times = await get_user_setting(user_id)
    logging.info(f"Обновляем расписание для пользователя {user_id}, times={times}")
    schedule_user(user_id, times)

async def schedule_jobs():
    """Первичное планирование при старте (для всех, кто уже в БД)."""
    user_ids = await get_all_users_with_settings()
    logging.info(f"Запускаем планирование для {len(user_ids)} пользователей")
    for uid in user_ids:
        times = await get_user_setting(uid)
        schedule_user(uid, times)

async def start_scheduler(bot_instance: Bot):
    global bot
    bot = bot_instance
    await schedule_jobs()
    scheduler.start()
