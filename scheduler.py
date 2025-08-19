import asyncio
import os
import random
import logging
from datetime import time
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from storage import get_all_users_with_settings, get_user_setting, get_random_question
from dotenv import load_dotenv
from state import user_state
load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")
bot = None

logging.basicConfig(level=logging.INFO)
scheduler = AsyncIOScheduler()

TIME_SLOTS = [time(19, 0), time(16, 0), time(12, 0) ]

async def send_daily_question(user_id: int):
    q = await get_random_question()
    if not q:
        return
    # Сохраняем текущий вопрос для пользователя
    user_state[user_id] = q.id
    print(user_state)
    try:
        await bot.send_message(chat_id=user_id, text=f"👀 {q.text}")
    except Exception as e:
        logging.warning(f"Не удалось отправить сообщение {user_id}: {e}")

async def schedule_jobs():
    user_ids = await get_all_users_with_settings()
    for uid in user_ids:
        # await send_daily_question(uid)
        times = await get_user_setting(uid)
        for i in range(times):
            if i < len(TIME_SLOTS):
                scheduler.add_job(
                    send_daily_question, "cron",
                    hour=TIME_SLOTS[i].hour, minute=TIME_SLOTS[i].minute,
                    args=[uid], id=f"user_{uid}_slot_{i}"
                )
                logging.info(f"Запланировано для {uid} на {TIME_SLOTS[i]}")


async def start_scheduler(bot_instance: Bot):
    global bot
    bot = bot_instance
    await schedule_jobs()
    scheduler.start()