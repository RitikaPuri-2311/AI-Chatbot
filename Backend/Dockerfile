# ==========================
# Builder Stage
# ==========================
FROM python:3.12-slim AS builder

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ==========================
# Runtime Stage
# ==========================
FROM python:3.12-slim AS runtime

WORKDIR /app

# Create non-root user
RUN useradd -m appuser

# Copy installed packages
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Give ownership to appuser
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]