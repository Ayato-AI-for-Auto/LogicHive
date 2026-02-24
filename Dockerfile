# Function Store MCP Backend Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
RUN pip install uv

# Copy the project files
COPY . .

# Install dependencies using uv
RUN uv pip install --system -e .

# Set environment variables
ENV FS_HOST=0.0.0.0
ENV FS_PORT=8080
ENV FS_TRANSPORT=http
ENV FS_DATA_DIR=/data

# Create data directory
RUN mkdir -p /data

# Expose the Cloud Run default port
EXPOSE 8080

# Run the backend server
# We use the RESTful FastAPI server (background_server.py) for the cloud version
CMD ["python", "backend/mcp_core/infra/background_server.py"]
