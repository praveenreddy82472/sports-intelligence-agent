# ===========================
# 1. Base image
# ===========================
FROM python:3.10-slim AS base

# Prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
# Prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1

# Create working directory
WORKDIR /app

# Install OS dependencies (for requests, uvicorn, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ===========================
# 2. Install Python packages
# ===========================
FROM base AS builder

COPY requirements.txt /app/requirements.txt

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# ===========================
# 3. Final runtime image
# ===========================
FROM python:3.10-slim

WORKDIR /app

# Copy installed Python packages
COPY --from=builder /usr/local/lib/python3.10 /usr/local/lib/python3.10
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy all application files
COPY . /app

# Expose port for Azure Container Apps
EXPOSE 8000

# Uvicorn start command
CMD ["uvicorn", "fastapi_app.main:app", "--host", "0.0.0.0", "--port", "8000"]
