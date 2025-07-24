@echo off

echo Attivazione ambiente virtuale...
call .\.venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Errore durante l'attivazione dell'ambiente virtuale.
    pause
    exit /b %errorlevel%
)

echo Avvio del test in modalita' DEBUG...
echo Assicurarsi che il server sia gia' in esecuzione (es. usando debug_server.bat).
echo.

python simple_test.py

echo.
echo Test terminato.
pause
echo === Test del server ===
echo.
python -u simple_test.py
pause
