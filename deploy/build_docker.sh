#!/bin/bash
set -e

echo "Verifying requirements.txt exists..."
if [ ! -f "backend/requirements.txt" ]; then
    echo "Error: backend/requirements.txt not found!"
    exit 1
fi

echo "Building Docker image..."
docker-compose build

echo "Starting containers..."
docker-compose up -d