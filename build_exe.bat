@echo off
echo [*] Installing PyInstaller...
pip install pyinstaller

echo [*] Building ZeroTraceFW (Single Executable)...
python -m PyInstaller --clean ^
  --name "ZeroTraceFW" ^
  --onefile ^
  --windowed ^
  --uac-admin ^
  --hidden-import="uvicorn" ^
  --hidden-import="uvicorn.logging" ^
  --hidden-import="uvicorn.loops" ^
  --hidden-import="uvicorn.loops.auto" ^
  --hidden-import="uvicorn.protocols" ^
  --hidden-import="uvicorn.protocols.http" ^
  --hidden-import="uvicorn.protocols.http.auto" ^
  --hidden-import="uvicorn.protocols.websockets" ^
  --hidden-import="uvicorn.protocols.websockets.auto" ^
  --hidden-import="uvicorn.lifespan" ^
  --hidden-import="uvicorn.lifespan.on" ^
  --hidden-import="uvicorn.lifespan.off" ^
  --hidden-import="fastapi" ^
  --hidden-import="sqlite3" ^
  --add-data "logo.png;." ^
  --icon="logo.png" ^
  --copy-metadata="fastapi" ^
  --copy-metadata="uvicorn" ^
  gui_app.py

echo [*] Build Complete! Check the 'dist' directory for ZeroTraceFW.exe
