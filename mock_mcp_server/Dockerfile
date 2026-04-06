FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir fastapi uvicorn pydantic

# Copy application
COPY main.py .

# Expose port
EXPOSE 8000

# Run server
CMD ["python", "main.py"]
