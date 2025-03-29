FROM python:3.10.4-slim

# Установим необходимые компиляторы и библиотеки
RUN apt-get update && \
    apt-get install -y build-essential clang gcc libatlas-base-dev liblapack-dev && \
    rm -rf /var/lib/apt/lists/*

# Установим зависимости
RUN pip install --upgrade pip setuptools wheel

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ /app/src/
COPY config.yaml /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

CMD ["python", "main.py"]