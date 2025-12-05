FROM python:3.10-slim

WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Запускаем webhook-сервер
CMD ["python", "main.py"]
