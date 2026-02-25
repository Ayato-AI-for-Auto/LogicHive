# --- Stage 1: Builder ---
FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv
RUN pip install uv

# Copy only dependency and source files needed for installation
COPY pyproject.toml .
COPY backend ./backend

# Install dependencies (system-wide inside the builder, we will copy the packages)
# Note: uv pip install --system is usually easiest, but we want a venv for clean copying
RUN uv venv && . .venv/bin/activate && uv pip install .

# --- Stage 2: Runtime ---
FROM python:3.12-slim

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy the backend source code
COPY backend /app/backend

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/backend"
ENV FS_HOST=0.0.0.0
ENV FS_PORT=8080
ENV FS_TRANSPORT=http
ENV FS_DATA_DIR=/tmp/logic_hive

# Expose the Cloud Run default port
EXPOSE 8080

# Run the backend server as a module
CMD ["python", "-m", "hub.app"]
