#!/bin/bash

# Exit on error
set -e

echo "Building Task Manager API..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "Please update the .env file with your configuration"
fi

# Build and start the containers
echo "Building Docker images..."
docker-compose build

echo "Starting services..."
docker-compose up -d

echo "Waiting for services to start..."
sleep 5

# Check if services are running
echo "Checking services..."
if docker-compose ps | grep -q "Up"; then
    echo "Services are running successfully!"
    echo "API is available at http://localhost:5000"
    echo "MongoDB is available at localhost:27017"
    echo "Redis is available at localhost:6379"
else
    echo "Error: Some services failed to start"
    docker-compose logs
    exit 1
fi 