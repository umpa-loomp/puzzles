# Quick launcher for puzzle chain finder
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Starting Puzzle Chain Finder..." -ForegroundColor Green
& "$scriptPath\deploy\run-docker.bat"