@echo off

echo Attivazione ambiente virtuale...
call .\.venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Errore durante l'attivazione dell'ambiente virtuale.
    pause
    exit /b %errorlevel%
)

echo Avvio del server...
python -u server.py

echo.
echo Il server e' stato terminato.
pause
