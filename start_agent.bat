@echo off

echo Attivazione ambiente virtuale...
call .\.venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Errore durante l'attivazione dell'ambiente virtuale.
    pause
    exit /b %errorlevel%
)

echo Avvio dell'agent...
python -u agent.py

echo.
echo L'agent e' stato terminato.
pause
