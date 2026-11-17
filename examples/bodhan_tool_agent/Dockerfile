# Production container image for Bodhan Tool Server and Task Agent
FROM python:3.11-slim

# Install system dependencies (ffmpeg for media processing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy pinned requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and project config
COPY . .

# Install editable package
RUN pip install --no-cache-dir -e . --no-deps

# Default environment
ENV PYTHONUNBUFFERED=1
ENV BODHAN_BASE_URL="https://api.bodhan.ai"

# Run tests by default on build verification, or launch MCP stdio server
CMD ["python", "-m", "bodhan_mcp"]
