# Build Stage
FROM python:3.11-slim-bookworm AS builder

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --frozen --no-dev --all-extras

# Runtime Stage
FROM python:3.11-slim-bookworm

# Install runtime dependencies (e.g., git for auto-backup)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed environment and source code
COPY --from=builder /app/.venv /app/.venv
COPY src /app/src

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=10880

# Expose the SSE port
EXPOSE 10880

# Default command
CMD ["python", "src/mcp_server.py"]
