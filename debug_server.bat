@echo off

echo Attivazione ambiente virtuale...
call .\.venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Errore durante l'attivazione dell'ambiente virtuale.
    pause
    exit /b %errorlevel%
)

echo Avvio del server in MODALITA' DEBUG...

rem Imposta la variabile d'ambiente per attivare il debug di Flask
set FLASK_DEBUG=1

python -u server.py

echo.
echo Il server e' stato terminato.
pause
echo === Avvio del server in modalita debug ===
echo.
python -u server.py
pause
