@echo off
rem デシベルメーターを GUI で起動する（コンソール窓は残さない）
cd /d "%~dp0"

if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" decibel_meter.py
) else (
    start "" pythonw decibel_meter.py
)
