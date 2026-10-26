@echo off
cd /d "%~dp0"
if not exist "%~dp0.venv\Scripts\pythonw.exe" (
    echo Ambiente Python nao encontrado.
    echo Crie o ambiente com: python -m venv .venv
    echo Instale com: .venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b 1
)
start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0iniciar_desktop.pyw"
