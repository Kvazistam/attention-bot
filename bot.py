import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.client.bot import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from dotenv import load_dotenv
from aiogram.types import FSInputFile
from storage import (
    init_db, seed_questions, get_random_question,
    save_answer, get_user_history, save_user_setting, get_user_setting
)

load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="Markdown"))
dp = Dispatcher()
from state import user_state


def main_menu():
    kb = ReplyKeyboardBuilder()
    kb.button(text="🧠 Задать вопрос")
    kb.button(text="📚 История за неделю")
    kb.button(text="⚙️ Настройки")
    kb.button(text="🌟 Приминг")
    return kb.as_markup(resize_keyboard=True)

def priming_menu():
    kb = ReplyKeyboardBuilder()
    options = [
        "Спокойствие", "Креатив", "Доверие", "Цели",
        "Рост", "Любовь", "Изобилие", "Смелость"
    ]
    for opt in options:
        kb.button(text=opt)
    kb.button(text="🔙 Назад")
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("Привет! Это бот для тренировки фильтра внимания 👁️", reply_markup=main_menu())

@dp.message(lambda msg: msg.text == "🧠 Задать вопрос")
async def ask_question(message: Message):
    q = await get_random_question()
    if not q:
        await message.answer("Нет доступных вопросов.")
        return
    user_state[message.from_user.id] = q.id
    await message.answer(q.text)

@dp.message(lambda msg: msg.text == "📚 История за неделю")
async def history(message: Message):
    hist = await get_user_history(message.from_user.id)
    if not hist:
        await message.answer("История пуста 📭")
        return
    reply = "📚 Ответы за 7 дней:\n\n"
    for ts, q_text, a_text in hist:
        reply += f"🕒 {ts.strftime('%d.%m %H:%M')}\n❓ {q_text}\n💬 {a_text}\n\n"
    await message.answer(reply)

@dp.message(lambda msg: msg.text == "⚙️ Настройки")
async def settings_menu(message: Message):
    kb = ReplyKeyboardBuilder()
    kb.button(text="0 раз в день")
    kb.button(text="1 раз в день")
    kb.button(text="2 раза в день")
    kb.button(text="3 раза в день")
    kb.button(text="🔙 Назад")
    await message.answer("Как часто присылать вопросы?", reply_markup=kb.as_markup(resize_keyboard=True))

@dp.message(lambda msg: msg.text in ["0 раз в день", "1 раз в день", "2 раза в день", "3 раза в день"])
async def save_setting(message: Message):
    count = int(message.text[0])
    await save_user_setting(message.from_user.id, count)
    await message.answer(f"✅ Буду спрашивать {count} раз в день", reply_markup=main_menu())

@dp.message(lambda msg: msg.text == "🌟 Приминг")
async def priming(message: Message):
    await message.answer("Выберите режим приминга 🌟", reply_markup=priming_menu())

@dp.message(lambda msg: msg.text in [
    "Спокойствие", "Креатив", "Доверие", "Цели",
    "Рост", "Любовь", "Изобилие", "Смелость"
])
async def priming_choice(message: Message):
    filename = f"priming/{message.text.lower()}.md"
    img_path = f"images/{message.text.lower()}.jpg"
    print(filename)
    if not os.path.exists(filename):
        await message.answer("Файл с текстом пока не добавлен.")
        return
    with open(filename, "r", encoding="utf-8") as f:
        text = f.read()
    if os.path.exists(img_path):
        photo = FSInputFile(img_path)
        await message.answer_photo(photo, caption=text)
    else:
        await message.answer(text, reply_markup=priming_menu())

@dp.message(lambda msg: msg.text == "🔙 Назад")
async def back(message: Message):
    await message.answer("Возврат в меню", reply_markup=main_menu())

@dp.message()
async def handle_answer(message: Message):
    uid = message.from_user.id
    username = message.from_user.username
    if uid not in user_state:
        print(user_state, uid)
        await message.answer(" Ответ не сохранён ", reply_markup=main_menu())
        return
    qid = user_state.pop(uid)
    await save_answer(uid, qid, message.text, username=username)
    await message.answer("✅ Ответ сохранён", reply_markup=main_menu())

async def main():
    from scheduler import start_scheduler
    await init_db()
    await seed_questions()
    asyncio.create_task(start_scheduler(bot))
    await dp.start_polling(bot)
    
    

if __name__ == "__main__":
    asyncio.run(main())
