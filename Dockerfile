FROM python:3.10-slim

WORKDIR /app

# Копируем ВСЕ файлы проекта внутрь контейнера
COPY . /app

# Обновляем pip
RUN pip install --upgrade pip

# Ставим зависимости
RUN pip install -r requirements.txt

# Запуск бота
CMD ["python", "main.py"]
