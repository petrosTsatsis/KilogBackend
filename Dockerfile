# 1. Base Image
FROM python:3.11-slim

# 2. Environment Variables
# Prevents Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
# Keeps Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 3. System Dependencies
# We need libpq-dev for Postgres and gcc for building some python extensions
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 4. Install Python Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy Application Code
COPY . .

# 6. Create a non-root user (Security Best Practice)
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser /app
USER appuser

# 7. Command to run the app
# We use --host 0.0.0.0 so the container is accessible from outside
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]