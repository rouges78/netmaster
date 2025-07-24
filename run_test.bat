@echo off

echo Attivazione ambiente virtuale...
call .\\.venv\\Scripts\\activate.bat
if %errorlevel% neq 0 (
    echo Errore durante l'attivazione dell'ambiente virtuale.
    pause
    exit /b %errorlevel%
)

echo Avvio del server in background...
start "Server" cmd /k "call .\\.venv\\Scripts\\activate.bat && python server.py"

echo Attesa di 5 secondi per l'avvio del server...
ping 127.0.0.1 -n 6 > nul

echo Avvio del test...
python simple_test.py
if %errorlevel% neq 0 (
    echo Errore durante l'esecuzione del test.
) else (
    echo Test eseguito con successo.
)

echo Premi un tasto per chiudere questa finestra...
pause
