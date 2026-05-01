FROM python:3.11-slim

WORKDIR /app

# System dependencies (PDF extraction + OCR)
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-fra \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
COPY . .
RUN pip install --no-cache-dir -e .

EXPOSE 8000 8501 8502
