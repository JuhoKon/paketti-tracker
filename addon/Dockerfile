ARG BUILD_FROM=ghcr.io/home-assistant/aarch64-base-python:3.12-alpine3.19

# Stage 1: Build frontend
FROM node:20-alpine AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Runtime
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

# Copy frontend build from stage 1
COPY --from=frontend-build /frontend/dist/ ./frontend/dist/

# Register as s6-overlay service
COPY run.sh /etc/services.d/paketti-tracker/run
RUN chmod a+x /etc/services.d/paketti-tracker/run

EXPOSE 8099
