@echo off
echo === Avvio del sistema di monitoraggio ===
echo.

echo Creazione directory data se non esiste...
if not exist "data" mkdir data

echo.
echo Avvio del server in una nuova finestra...
start "Server" cmd /k "call .\.venv\Scripts\activate.bat && python -u server.py"

echo Attesa inizializzazione server...
ping 127.0.0.1 -n 6 > nul

echo.
echo Avvio dell'agent in una nuova finestra...
start "Agent" cmd /k "call .\.venv\Scripts\activate.bat && python -u agent.py"

echo.
echo Avvio dell'interfaccia grafica in una nuova finestra...
start "Monitor" cmd /k "call .\.venv\Scripts\activate.bat && python -u monitor_gui.py"

echo.
echo Sistema avviato! I componenti sono stati aperti in finestre separate.
echo Questa finestra puo' essere chiusa.
pause
