FROM python:3.9-slim

WORKDIR /transneft

# Установка системных зависимостей для компиляции Python пакетов
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    portaudio19-dev \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip

# Установка всех пакетов из requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data evaluation results vector_stores

ENV PYTHONPATH=/transneft
ENV PYTHONUNBUFFERED=1

CMD ["python", "run_system.py"]