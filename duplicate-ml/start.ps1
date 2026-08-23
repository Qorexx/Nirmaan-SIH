# Start the MPLADS Duplicate Detection ML Service
# Run from SIH root: .\duplicate-ml\start.ps1
# Or from duplicate-ml/: .\start.ps1

Write-Host ""
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "  MPLADS Duplicate & Similarity Detection AI Service" -ForegroundColor Cyan
Write-Host "  Starting on http://localhost:8000" -ForegroundColor Cyan
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $PSScriptRoot
uvicorn app:app --reload --host 0.0.0.0 --port 8000
