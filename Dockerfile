FROM python:3.11-slim

# Set working directory consistently
WORKDIR /app

# Install system dependencies including netcat for the wait script
RUN apt-get update && apt-get install -y \
    gcc \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the wait script
# COPY wait-for-kafka.sh /wait-for-kafka.sh
# RUN chmod +x /wait-for-kafka.sh

# Copy application code
COPY . .

EXPOSE 8000

# Use the wait script before starting the application
# CMD ["/wait-for-kafka.sh", "kafka", "9092", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]