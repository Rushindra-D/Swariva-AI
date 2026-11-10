FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose standard port
EXPOSE 8000

ENV APP_ENV=production
ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

