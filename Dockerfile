# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy initial database (will be copied to volume if volume is empty)
COPY data/anime.db ./initial_anime.db

# Create data directory and set permissions
RUN mkdir -p /app/data && chmod 777 /app/data

# Copy startup script
COPY docker-startup.sh /app/
RUN chmod +x /app/docker-startup.sh

# Expose port
EXPOSE 8000

# Use startup script
CMD ["/app/docker-startup.sh"]
