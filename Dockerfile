# -----------------------------------------------------
FROM python:3.12.10-bullseye

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy project
COPY . .

# Copy and make entrypoint executable
COPY entrypoint.sh .
COPY wait-for-it.sh .
RUN chmod +x entrypoint.sh wait-for-it.sh

EXPOSE 8000

CMD ["./entrypoint.sh"]
