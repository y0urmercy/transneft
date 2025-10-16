FROM python:3.9-slim

WORKDIR /transneft

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data evaluation results vector_stores

ENV PYTHONPATH=/transneft
ENV PYTHONUNBUFFERED=1

CMD ["python", "run_system.py"]