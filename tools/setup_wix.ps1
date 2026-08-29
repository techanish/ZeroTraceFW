$ErrorActionPreference = "Stop"
$wixUrl = "https://github.com/wixtoolset/wix3/releases/download/wix3112rtm/wix311-binaries.zip"
$toolsDir = Join-Path $PSScriptRoot "wix"
$zipFile = Join-Path $PSScriptRoot "wix.zip"

if (-not (Test-Path $toolsDir)) {
    Write-Host "Downloading WiX Toolset..."
    Invoke-WebRequest -Uri $wixUrl -OutFile $zipFile
    Write-Host "Extracting WiX Toolset..."
    Expand-Archive -Path $zipFile -DestinationPath $toolsDir -Force
    Remove-Item $zipFile
    Write-Host "WiX Toolset installed to $toolsDir"
} else {
    Write-Host "WiX Toolset already installed in $toolsDir"
}
