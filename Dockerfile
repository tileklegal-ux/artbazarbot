FROM python:3.10-slim

WORKDIR /app

# Копируем requirements.txt в текущую WORKDIR
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем ВСЕ файлы проекта в контейнер
COPY . .

# Запускаем бота
CMD ["python", "main.py"]
