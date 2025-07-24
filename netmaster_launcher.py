#!/usr/bin/env python3
"""
NetMaster Monitoring Suite - Launcher EXE
Launcher principale per eseguibile Windows
"""

import os
import sys
import logging
from pathlib import Path

# Aggiungi directory corrente al path per importazioni
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def setup_exe_environment():
    """Configura ambiente per eseguibile."""
    # Imposta directory di lavoro
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller bundle
        os.chdir(sys._MEIPASS)
    else:
        # Sviluppo
        os.chdir(current_dir)
    
    # Configura variabili d'ambiente se non presenti
    env_vars = {
        'NETMASTER_USERNAME': 'admin',
        'NETMASTER_PASSWORD_HASH': '$2b$12$H5DowkEAanaIQbXx2zFnhe9YAs64KYcdVPWu0a.9pbQp9mOhzo1dW',
        'USE_HTTPS': 'false',  # Disabilita HTTPS per semplicità
        'NETMASTER_HOST': '127.0.0.1',
        'NETMASTER_PORT': '5000',
        'LOG_LEVEL': 'INFO'
    }
    
    for key, value in env_vars.items():
        if key not in os.environ:
            os.environ[key] = value

def main():
    """Funzione principale launcher."""
    try:
        print("=" * 60)
        print("NetMaster Monitoring Suite - Eseguibile Windows")
        print("=" * 60)
        print("Avvio server NetMaster...")
        print("Dashboard disponibile su: http://127.0.0.1:5000")
        print("Credenziali: admin / password")
        print("=" * 60)
        
        # Setup ambiente
        setup_exe_environment()
        
        # Importa e avvia server
        from server_integrated import app
        
        # Configura Flask per produzione
        app.config['DEBUG'] = False
        app.config['TESTING'] = False
        
        # Avvia server
        print("Server NetMaster avviato!")
        print("Premi Ctrl+C per arrestare il server")
        
        app.run(
            host=os.getenv('NETMASTER_HOST', '127.0.0.1'),
            port=int(os.getenv('NETMASTER_PORT', 5000)),
            threaded=True,
            use_reloader=False
        )
        
    except KeyboardInterrupt:
        print("\nServer arrestato dall'utente")
    except Exception as e:
        print(f"Errore avvio NetMaster: {e}")
        input("Premi Enter per chiudere...")
        sys.exit(1)

if __name__ == "__main__":
    main()
