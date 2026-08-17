@echo off
echo [*] Step 1: Building the main ZeroTraceFS application (ZeroTraceFW.exe)...
call build_exe.bat
if %errorlevel% neq 0 exit /b %errorlevel%

echo [*] Step 2: Packaging the Setup Wizard into a standalone installer...
python -m PyInstaller --clean ^
  --name "ZeroTraceFS_Setup" ^
  --onefile ^
  --windowed ^
  --icon="logo.png" ^
  --add-data "dist\ZeroTraceFW.exe;." ^
  --add-data "logo.png;." ^
  installer.py

echo [*] Build Complete! You can find the standalone installer at 'dist\ZeroTraceFS_Setup.exe'
