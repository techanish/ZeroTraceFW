@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=amd64 -host_arch=amd64 >nul 2>&1
set PATH=%USERPROFILE%\.cargo\bin;%PATH%
set PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
cd /d E:\Projects\ZeroTraceFS\ztfs_engine
cargo build --release
