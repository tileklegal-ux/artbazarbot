FROM python:3.10-slim

WORKDIR /app

# Копируем проект
COPY . /app

# Обновляем pip
RUN pip install --upgrade pip

# Устанавливаем зависимости
RUN pip install -r requirements.txt

# Запуск
CMD ["python", "main.py"]
