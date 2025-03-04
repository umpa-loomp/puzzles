@echo off
echo Starting Puzzle Chain Finder...
docker-compose up -d
echo.
echo Application is running!
echo.
echo Open your browser and navigate to: http://localhost:8080
echo.
echo Press Ctrl+C to stop viewing logs
echo Close this window to keep the application running in the background
echo.
echo To stop the application, run: docker-compose down
docker-compose logs -f