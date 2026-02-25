# --- Stage 1: Builder ---
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1    
WORKDIR /app

# Pure Stateless Hub requires strictly minimal dependencies.
# We explicitly EXCLUDE heavy Edge packages like duckdb, google-genai, and fastmcp.
RUN uv venv && uv pip install fastapi uvicorn PyGithub python-dotenv ruff bandit safety httpx

# --- Stage 2: Runtime ---
FROM python:3.12-slim

WORKDIR /app

# Copy the pre-built, ultra-light virtual environment
COPY --from=builder /app/.venv /app/.venv

# Copy only the necessary backend source logic
COPY backend /app/backend

# Configure Env
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/backend"
ENV FS_HOST=0.0.0.0
ENV FS_PORT=8080

EXPOSE 8080

CMD ["python", "-m", "hub.app"]
