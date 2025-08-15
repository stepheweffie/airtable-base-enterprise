#!/bin/bash

# Mercor Airtable Automation - Quick Deployment Script

set -e

echo "Mercor Airtable Automation - Deployment Script"
echo "=================================================="

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "ERROR: Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "SUCCESS: Docker is running"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "WARNING: .env file not found. Creating from example..."
    cp .env.example .env
    echo "INFO: Please edit .env file with your actual API credentials before deployment"
    echo "   Required: AIRTABLE_API_KEY, AIRTABLE_BASE_ID, OPENAI_API_KEY"
    exit 1
fi

echo "SUCCESS: Environment file found"

# Build the Docker image
echo "INFO: Building Docker image..."
docker build -t mercor-automation:latest .

echo "SUCCESS: Docker image built successfully"

# Run with docker-compose
echo "INFO: Starting application with docker-compose..."
docker-compose up -d

echo "SUCCESS: Application started successfully"

# Show status
echo "INFO: Container status:"
docker-compose ps

echo ""
echo "SUCCESS: Deployment complete!"
echo ""
echo "Available commands:"
echo "  docker-compose logs -f mercor-automation  # View logs"
echo "  docker-compose exec mercor-automation python main.py status  # Check status"
echo "  docker-compose exec mercor-automation python main.py pipeline  # Run pipeline"
echo "  docker-compose down  # Stop all services"
echo ""
echo "For more information, see README.md"
