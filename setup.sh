#!/bin/bash
set -e

echo "=== Motherbrain MCP Setup ==="
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check Docker Compose
if ! docker compose version &> /dev/null && ! docker-compose version &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose found"

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file..."
    cp .env.example .env
    echo "✅ .env created from .env.example"
    
    # Prompt for API key
    echo ""
    read -p "Enter API key (or press Enter to use default 'supersecret'): " api_key
    if [ ! -z "$api_key" ]; then
        sed -i.bak "s/API_KEY=supersecret/API_KEY=$api_key/" .env
        rm -f .env.bak
        echo "✅ API key updated"
    else
        echo "Using default API key (change this in production!)"
    fi
else
    echo "✅ .env already exists, skipping creation"
fi

echo ""
echo "=== Setup complete! ==="
echo ""
echo "To start with local build:"
echo "  docker compose up -d"
echo ""
echo "Or use pre-built images (faster):"
echo "  docker compose -f docker-compose.deploy.yml up -d"
echo ""
echo "Then open:"
echo "  Dashboard: http://localhost:3000"
echo "  API docs:  http://localhost:8000/docs"
