import sqlite3
import os

# Создание файла базы данных, если его нет
DB_NAME = "user_settings.db"

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Создаём таблицу, если не существует
cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        user_id INTEGER PRIMARY KEY,
        times_per_day INTEGER
    )
""")
conn.commit()
conn.close()


# ✅ Сохранить настройку
def save_user_setting(user_id: int, times_per_day: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO settings (user_id, times_per_day)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET times_per_day=excluded.times_per_day
    """, (user_id, times_per_day))

    conn.commit()
    conn.close()


# 📤 Получить настройку (по умолчанию — 1 раз)
def get_user_setting(user_id: int) -> int:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT times_per_day FROM settings WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()

    conn.close()

    return result[0] if result else 1
