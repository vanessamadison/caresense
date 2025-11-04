# syntax=docker/dockerfile:1.7
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    ninja-build \
    libgomp1 \
    libomp-dev \
    tesseract-ocr \
    libgmp-dev \
    libmpfr-dev \
    libboost-program-options-dev \
    libboost-system-dev \
    libboost-serialization-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080
ENV UVICORN_WORKERS=4
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
