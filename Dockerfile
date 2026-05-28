FROM python:3.11-slim

WORKDIR /app

# System deps for building some Python packages (neo4j driver, cryptography)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (cached layer, rebuild only if requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY main.py .
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY docker/ ./docker/

RUN chmod +x docker/entrypoint.sh

# HF Spaces serves on port 7860 by default
EXPOSE 7860

ENTRYPOINT ["bash", "docker/entrypoint.sh"]
