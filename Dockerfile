FROM python:3.11-slim

# рабочая директория внутри контейнера
WORKDIR /app

# устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# копируем код
COPY . .

# команда запуска — bot.py (шедулер внутри него сам стартует)
CMD ["python", "bot.py"]
