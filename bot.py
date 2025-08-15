import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from gsheet import save_response, get_user_history
from storage import save_user_setting, get_user_setting
import os
from dotenv import load_dotenv

load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# 📋 Главное меню
def main_menu():
    kb = ReplyKeyboardBuilder()
    kb.button(text="🧠 Задать вопрос")
    kb.button(text="📚 История за неделю")
    kb.button(text="⚙️ Настройки")
    return kb.as_markup(resize_keyboard=True)

# 🏁 Старт
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("Привет! Это бот для тренировки фильтра внимания 👁️", reply_markup=main_menu())

# 🧠 Ответ на вопрос
@dp.message(lambda msg: msg.text == "🧠 Задать вопрос")
async def ask_question(message: Message):
    question = "Что хорошего было сегодня?"  # пока один вопрос
    await message.answer(question)
    dp.workflow_data[user_id := message.from_user.id] = {
        "current_question": question
    }

# 💬 Обработка ответа
@dp.message()
async def handle_answer(message: Message):
    user_id = message.from_user.id
    data = dp.workflow_data.get(user_id)

    if not data or "current_question" not in data:
        return  # ничего не делать

    question = data["current_question"]
    answer = message.text

    save_response(user_id, message.from_user.username, question, answer)
    await message.answer("✅ Ответ сохранён", reply_markup=main_menu())
    dp.workflow_data.pop(user_id, None)

# 📚 История
@dp.message(lambda msg: msg.text == "📚 История за неделю")
async def history(message: Message):
    user_id = message.from_user.id
    history = get_user_history(user_id)

    if not history:
        await message.answer("История пуста 📭")
        return

    reply = "📚 Ответы за 7 дней:\n\n"
    for entry in history:
        reply += f"🕒 {entry['timestamp']}\n❓ {entry['question']}\n💬 {entry['answer']}\n\n"
    await message.answer(reply)

# ⚙️ Настройки
@dp.message(lambda msg: msg.text == "⚙️ Настройки")
async def settings_menu(message: Message):
    kb = ReplyKeyboardBuilder()
    kb.button(text="1 раз в день")
    kb.button(text="2 раза в день")
    kb.button(text="3 раза в день")
    kb.button(text="🔙 Назад")
    await message.answer("Как часто присылать вопросы?", reply_markup=kb.as_markup(resize_keyboard=True))

# ✅ Сохранение настройки
@dp.message(lambda msg: msg.text in ["1 раз в день", "2 раза в день", "3 раза в день"])
async def save_setting(message: Message):
    user_id = message.from_user.id
    count = int(message.text[0])
    save_user_setting(user_id, count)
    await message.answer(f"✅ Буду спрашивать {count} раз в день", reply_markup=main_menu())

# 🔙 Назад
@dp.message(lambda msg: msg.text == "🔙 Назад")
async def back(message: Message):
    await message.answer("Возврат в меню", reply_markup=main_menu())

# ▶️ Запуск
if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
