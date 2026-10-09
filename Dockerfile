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
RUN pip install --no-cache-dir setuptools && pip install --no-cache-dir .

# Run unprivileged: the compute agent's sandbox child inherits this user, so as
# root an escape from it would own the container. The code under /app stays
# root-owned and read-only; only the model cache (a volume) and the bind-mounted
# data/chroma are written to. The UID is fixed because the host must chown
# data/chroma to it — see scripts/deploy_ci.sh.
RUN groupadd --gid 10001 senstat \
    && useradd --uid 10001 --gid senstat --create-home senstat \
    && mkdir -p /home/senstat/.cache/huggingface \
    && chown -R senstat:senstat /home/senstat/.cache
ENV HF_HOME=/home/senstat/.cache/huggingface
USER senstat

EXPOSE 8000 8501 8502
