# Используем официальный образ Python
FROM python:3.10-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы в контейнер
COPY . /app

# Обновляем pip
RUN pip install --upgrade pip

# Устанавливаем зависимости
RUN pip install -r requirements.txt

# Открываем порт (хоть боту не нужен, Fly требует)
EXPOSE 8080

# Команда запуска
CMD ["python", "main.py"]
