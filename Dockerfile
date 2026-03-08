# Asset Lens - Personal Asset Operating System
# Dockerfile for production deployment

FROM python:3.11-slim

LABEL maintainer="Asset Lens Team"
LABEL description="Personal Asset Operating System"
LABEL version="1.0.0"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Shanghai

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/output /app/cache /app/logs /app/data

# Set permissions
RUN chmod +x /app/scripts/*.sh 2>/dev/null || true

# Expose port (for future web interface)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import asset_lens; print('OK')" || exit 1

# Default command
CMD ["python", "-m", "asset_lens", "--help"]
