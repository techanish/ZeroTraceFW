@echo off
echo [*] Step 1: Downloading WiX Toolset...
powershell -ExecutionPolicy Bypass -File "tools\setup_wix.ps1"

echo [*] Step 2: Building ZeroTraceFW.exe...
call build_exe.bat
if %errorlevel% neq 0 exit /b %errorlevel%

echo [*] Step 3: Compiling WiX XML (candle.exe)...
tools\wix\candle.exe ZeroTraceFS.wxs -o dist\ZeroTraceFS.wixobj
if %errorlevel% neq 0 exit /b %errorlevel%

echo [*] Step 4: Linking MSI (light.exe)...
tools\wix\light.exe -ext WixUIExtension dist\ZeroTraceFS.wixobj -o dist\ZeroTraceFS.msi -spdb
if %errorlevel% neq 0 exit /b %errorlevel%

echo [*] Build Complete! The MSI is located at dist\ZeroTraceFS.msi
