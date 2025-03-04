<#
.SYNOPSIS
    Fetches and processes puzzle data from the API or local files.
.DESCRIPTION
    This script can retrieve puzzle data either from the running API container
    or directly from data files. It supports filtering, analyzing chains, and 
    exporting results in various formats.
.PARAMETER Source
    The source of the puzzle data: "api" (default) or "file"
.PARAMETER File
    When Source is "file", specifies the data file to use (default: "source.txt")
.PARAMETER OutputFormat
    Format for output: "json", "csv", or "text" (default)
.EXAMPLE
    .\get-puzzle.ps1 -Source api
    Retrieves puzzles from the running API container
.EXAMPLE
    .\get-puzzle.ps1 -Source file -File "backend/data/medium_connected.txt" -OutputFormat json
    Loads puzzles from the specified file and outputs in JSON format
#>

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("api", "file")]
    [string]$Source = "api",
    
    [Parameter(Mandatory=$false)]
    [string]$File = "backend/data/source.txt",
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("json", "csv", "text")]
    [string]$OutputFormat = "text"
)

function Get-PuzzlesFromAPI {
    Write-Host "Fetching puzzles from API..." -ForegroundColor Cyan
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:5000/api/puzzles" -Method Get
        return $response
    }
    catch {
        Write-Host "Error connecting to API: $_" -ForegroundColor Red
        Write-Host "Make sure the Docker container is running using deploy/run-docker.bat" -ForegroundColor Yellow
        exit 1
    }
}

function Get-PuzzlesFromFile {
    param(
        [string]$FilePath
    )
    
    Write-Host "Loading puzzles from file: $FilePath" -ForegroundColor Cyan
    
    if (-not (Test-Path $FilePath)) {
        Write-Host "Error: File not found at $FilePath" -ForegroundColor Red
        exit 1
    }
    
    try {
        $puzzles = @()
        $lines = Get-Content $FilePath
        
        foreach ($line in $lines) {
            if (-not [string]::IsNullOrWhiteSpace($line)) {
                $parts = $line -split '\s+'
                if ($parts.Count -ge 2) {
                    $puzzles += [PSCustomObject]@{
                        id = $parts[0]
                        connections = $parts[1..($parts.Count-1)]
                    }
                }
            }
        }
        
        return $puzzles
    }
    catch {
        Write-Host "Error processing file: $_" -ForegroundColor Red
        exit 1
    }
}

function Find-LongestChain {
    param(
        [array]$Puzzles
    )
    
    Write-Host "Analyzing longest chain..." -ForegroundColor Cyan
    
    # Simple chain finder algorithm for demonstration
    $puzzleDict = @{}
    foreach ($puzzle in $Puzzles) {
        $puzzleDict[$puzzle.id] = $puzzle
    }
    
    $visited = @{}
    $longest = @()
    
    foreach ($puzzle in $Puzzles) {
        $visited.Clear()
        $path = @()
        Find-Chain -PuzzleId $puzzle.id -Path ([ref]$path) -Visited ([ref]$visited) -PuzzleDict $puzzleDict
        
        if ($path.Count -gt $longest.Count) {
            $longest = $path.Clone()
        }
    }
    
    return $longest
}

function Find-Chain {
    param(
        [string]$PuzzleId,
        [ref]$Path,
        [ref]$Visited,
        [hashtable]$PuzzleDict
    )
    
    if ($Visited.Value.ContainsKey($PuzzleId)) {
        return
    }
    
    $Visited.Value[$PuzzleId] = $true
    $Path.Value += $PuzzleId
    
    $puzzle = $PuzzleDict[$PuzzleId]
    foreach ($conn in $puzzle.connections) {
        if ($PuzzleDict.ContainsKey($conn) -and -not $Visited.Value.ContainsKey($conn)) {
            Find-Chain -PuzzleId $conn -Path $Path -Visited $Visited -PuzzleDict $PuzzleDict
            break  # Only follow the first valid path for simplicity
        }
    }
}

function Format-Output {
    param(
        [array]$Data,
        [string]$Format
    )
    
    switch ($Format) {
        "json" {
            return $Data | ConvertTo-Json -Depth 10
        }
        "csv" {
            return $Data | ConvertTo-Csv -NoTypeInformation
        }
        "text" {
            $output = ""
            foreach ($item in $Data) {
                $output += "Puzzle ID: $($item)`n"
            }
            return $output
        }
        default {
            return $Data
        }
    }
}

# Main execution
if ($Source -eq "api") {
    $puzzles = Get-PuzzlesFromAPI
} else {
    $puzzles = Get-PuzzlesFromFile -FilePath $File
}

Write-Host "Found $($puzzles.Count) puzzles" -ForegroundColor Green

# Find the longest chain
$longestChain = Find-LongestChain -Puzzles $puzzles

# Output the results
Write-Host "`nLongest Chain Found: $($longestChain.Count) puzzles" -ForegroundColor Green
$formattedOutput = Format-Output -Data $longestChain -Format $OutputFormat
Write-Output $formattedOutput

# Save results to a file in the exports directory
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$exportFile = "exports/chain-$timestamp.$OutputFormat"
New-Item -Path "exports" -ItemType Directory -Force | Out-Null
$formattedOutput | Out-File -FilePath $exportFile
Write-Host "`nResults saved to: $exportFile" -ForegroundColor Cyan