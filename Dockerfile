#####################################################################
# Stage 1: Build Frontend
#####################################################################
FROM node:18-slim AS frontend-builder

# Set working directory
WORKDIR /app/frontend

# Copy package files and install dependencies
COPY frontend/package*.json ./
RUN npm ci

# Copy frontend source and build
COPY frontend/ ./
RUN npm run build

#####################################################################
# Stage 2: Build Backend Runtime
#####################################################################
FROM python:3.11-slim

# Set labels for Home Assistant add-on
LABEL io.hass.version="1.0.0" \
      io.hass.type="addon" \
      io.hass.arch="aarch64|amd64|armv7"

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Set up application directory
WORKDIR /app

# Copy and install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend from builder stage
COPY --from=frontend-builder /app/frontend/dist ./backend/static

# Create data directory
RUN mkdir -p /data

# Copy startup script and make executable
COPY run.sh /app/
RUN chmod +x /app/run.sh

# Expose port for Ingress
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health').read()" || exit 1

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Run the application
CMD ["/app/run.sh"]
