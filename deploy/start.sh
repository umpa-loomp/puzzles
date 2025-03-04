#!/bin/bash
set -e

# Debug output
set -x

# Show environment and permissions
echo "--- Debug Info ---"
echo "Current user: $(whoami)"
echo "Current directory: $(pwd)"
ls -la /app/data
echo "----------------"

# Verify source.txt exists and is readable
if [ ! -r "/app/data/source.txt" ]; then
    echo "Error: source.txt not found or not readable in /app/data/"
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p /app/logs /app/exports

# Start Nginx in background
nginx -g "daemon off;" &

# Start Flask application with debug mode
cd /app && FLASK_DEBUG=1 python -u main.py