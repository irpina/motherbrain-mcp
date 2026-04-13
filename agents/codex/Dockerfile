# Motherbrain Codex Agent
# This container runs an OpenAI Codex-powered agent connected to Motherbrain MCP

FROM python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --no-cache-dir \
    openai \
    httpx

# Create app directory
WORKDIR /app

# Copy agent code
COPY agent.py /app/agent.py

# Environment variables (set at runtime)
ENV OPENAI_API_KEY=""
ENV MCP_SERVER_URL=""
ENV MCP_API_KEY=""
ENV CHANNEL="general"
ENV TASK=""
ENV AGENT_NAME="codex"

# Run the agent
CMD ["python", "/app/agent.py"]
