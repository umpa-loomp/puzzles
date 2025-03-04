@echo off
echo Verifying requirements.txt exists...
if not exist "backend\requirements.txt" (
    echo Error: backend\requirements.txt not found!
    exit /b 1
)

echo Building Docker image...
docker-compose build

echo Starting containers...
docker-compose up -d