FROM python:3.10-slim

WORKDIR /app

# Открываем PORT, чтобы Fly думал что это web app
ENV PORT=8080
EXPOSE 8080

COPY . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["python", "main.py"]
