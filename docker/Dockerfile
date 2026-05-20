FROM python:3.11-slim as builder
WORKDIR /app
RUN apt-get update && apt-get install -y gcc postgresql-client && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*
COPY --from=builder /root/.local /home/appuser/.local
COPY --chown=appuser:appuser . .
ENV PATH=/home/appuser/.local/bin:$PATH PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
USER appuser
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]