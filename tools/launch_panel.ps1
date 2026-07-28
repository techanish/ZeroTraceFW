# Launch control panel with error capture
$ErrorActionPreference = "Continue"

try {
    Write-Host "Launching ZeroTraceFW Control Panel..." -ForegroundColor Cyan
    Write-Host "Path: d:\ZeroTraceFW\tools\ztfs_control_panel.ps1" -ForegroundColor Gray
    Write-Host ""
    
    & "d:\ZeroTraceFW\tools\ztfs_control_panel.ps1" -ProjectRoot "d:\ZeroTraceFW"
    
} catch {
    Write-Host ""
    Write-Host "ERROR OCCURRED:" -ForegroundColor Red
    Write-Host "Message: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "Line: $($_.InvocationInfo.ScriptLineNumber)" -ForegroundColor Yellow
    Write-Host "Position: $($_.InvocationInfo.PositionMessage)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Full Error:" -ForegroundColor Red
    Write-Host $_.Exception.ToString() -ForegroundColor Gray
}
