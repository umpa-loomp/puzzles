#!/bin/bash
echo "Starting Puzzle Chain Finder..."
docker-compose up -d
echo ""
echo "Application is running!"
echo ""
echo "Open your browser and navigate to: http://localhost:8080"  # Changed port from 80 to 8080
echo ""
echo "Press Ctrl+C to stop viewing logs"
echo "The application will continue running in the background"
echo ""
echo "To stop the application, run: docker-compose down"
docker-compose logs -f