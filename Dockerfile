# ==============================================================================
# OmniSynapse-Titan Enterprise Production Container
# ==============================================================================
FROM python:3.11-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt
RUN pip install --no-cache-dir --user pytest duckdb networkx

# Stage 2: Runtime image
FROM python:3.11-slim as runner

WORKDIR /app

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV RUN_MODE=local

COPY src/ ./src/
COPY data/ ./data/
COPY tests/ ./tests/
COPY run_tests.py .
COPY .env.example .env

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
