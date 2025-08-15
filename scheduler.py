import asyncio
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, time
from storage import get_user_setting
from gsheet import save_response
import logging
import random
import os

from dotenv import load_dotenv
load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
bot = Bot(token=API_TOKEN)

# Пример списка вопросов (можно вынести в отдельный файл или Google Таблицу)
QUESTIONS = [
    "Что сегодня получилось особенно хорошо?",
    "Что вызвало у тебя радость или благодарность?",
    "Какую возможность ты сегодня заметил?",
    "В чём сегодня ты почувствовал(а) силу, ясность, поддержку?"
]

# Настраиваем логгирование
logging.basicConfig(level=logging.INFO)
scheduler = AsyncIOScheduler()


# Время запуска (можно кастомизировать)
TIME_SLOTS = [time(9, 0), time(14, 0), time(19, 0)]


# 📤 Отправка вопроса пользователю
async def send_daily_question(user_id: int):
    question = random.choice(QUESTIONS)
    try:
        await bot.send_message(chat_id=user_id, text=f"👀 {question}")
    except Exception as e:
        logging.warning(f"❌ Не удалось отправить сообщение пользователю {user_id}: {e}")


# 📆 Расписание отправок на основе user_settings
async def schedule_jobs():
    logging.info("🕓 Планирование задач...")

    # Пример: список user_id из таблицы (можно заменить на свою систему хранения активных пользователей)
    user_ids = [row[0] for row in get_all_users_with_settings()]  # список всех user_id, у кого есть настройки

    for user_id in user_ids:
        times = get_user_setting(user_id)
        for i in range(times):
            if i < len(TIME_SLOTS):
                scheduler.add_job(send_daily_question, "cron",
                    hour=TIME_SLOTS[i].hour,
                    minute=TIME_SLOTS[i].minute,
                    args=[user_id],
                    id=f"user_{user_id}_slot_{i}")


def get_all_users_with_settings():
    import sqlite3
    conn = sqlite3.connect("user_settings.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM settings")
    result = cursor.fetchall()
    conn.close()
    return result


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(schedule_jobs())
    scheduler.start()
    logging.info("📡 Шедулер запущен")
    loop.run_forever()
