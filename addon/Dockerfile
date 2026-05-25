ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-python:3.12-alpine3.19
FROM ${BUILD_FROM}

# Install system dependencies for aiosqlite and aioimaplib
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Copy frontend build (built externally)
COPY frontend/dist/ ./frontend/dist/

# Copy entry point
COPY run.sh /run.sh
RUN chmod a+x /run.sh

EXPOSE 8099

CMD ["/run.sh"]
