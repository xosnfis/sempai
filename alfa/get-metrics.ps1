# PowerShell скрипт для работы с метриками API
# Использование: .\get-metrics.ps1

param(
    [int]$Days = 7,
    [string]$Category = "",
    [string]$Metric = "",
    [string]$Action = "summary"  # summary, calculate, get
)

$BaseUrl = "http://localhost:8000/api/metrics"

function Get-MetricsSummary {
    param([int]$Days)
    
    $url = "$BaseUrl/summary/?days=$Days"
    Write-Host "Getting metrics summary for $Days days..." -ForegroundColor Cyan
    Write-Host "URL: $url" -ForegroundColor Gray
    
    try {
        $response = Invoke-RestMethod -Uri $url -Method GET
        $response | ConvertTo-Json -Depth 10
    }
    catch {
        Write-Host "Error: $_" -ForegroundColor Red
        $_.Exception.Response
    }
}

function Calculate-Metrics {
    param([int]$Days)
    
    $url = "$BaseUrl/calculate/"
    $body = @{
        days = $Days
    } | ConvertTo-Json
    
    Write-Host "Calculating metrics for $Days days..." -ForegroundColor Cyan
    Write-Host "URL: $url" -ForegroundColor Gray
    
    try {
        $response = Invoke-RestMethod -Uri $url -Method POST -ContentType "application/json" -Body $body
        $response | ConvertTo-Json -Depth 10
    }
    catch {
        Write-Host "Error: $_" -ForegroundColor Red
        $_.Exception.Response
    }
}

function Get-Metrics {
    param([int]$Days, [string]$Category, [string]$Metric)
    
    $url = "$BaseUrl/?days=$Days"
    if ($Category) {
        $url += "&category=$Category"
    }
    if ($Metric) {
        $url += "&metric=$Metric"
    }
    
    Write-Host "Getting metrics..." -ForegroundColor Cyan
    Write-Host "URL: $url" -ForegroundColor Gray
    
    try {
        $response = Invoke-RestMethod -Uri $url -Method GET
        $response | ConvertTo-Json -Depth 10
    }
    catch {
        Write-Host "Error: $_" -ForegroundColor Red
        $_.Exception.Response
    }
}

# Выполнение в зависимости от действия
switch ($Action.ToLower()) {
    "summary" {
        Get-MetricsSummary -Days $Days
    }
    "calculate" {
        Calculate-Metrics -Days $Days
    }
    "get" {
        Get-Metrics -Days $Days -Category $Category -Metric $Metric
    }
    default {
        Write-Host "Unknown action: $Action" -ForegroundColor Red
        Write-Host "Available actions: summary, calculate, get" -ForegroundColor Yellow
    }
}

