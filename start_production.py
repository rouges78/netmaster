#!/usr/bin/env python3
"""
NetMaster Monitoring Suite - Avvio Produzione
Script per avviare NetMaster in ambiente di produzione
"""

import os
import sys
import signal
import logging
import threading
import time
from datetime import datetime
from production_config import ProductionConfig, get_production_config

# Importa il server integrato
from server_integrated import app, database

class ProductionServer:
    """Gestore server produzione NetMaster."""
    
    def __init__(self):
        self.config = get_production_config()
        self.logger = ProductionConfig.setup_production_logging()
        self.running = False
        self.backup_thread = None
        
    def setup_signal_handlers(self):
        """Configura gestori segnali per shutdown graceful."""
        def signal_handler(signum, frame):
            self.logger.info(f"Ricevuto segnale {signum}, avvio shutdown...")
            self.shutdown()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def setup_database_backup(self):
        """Configura backup automatico database."""
        def backup_worker():
            while self.running:
                try:
                    # Backup ogni ora
                    time.sleep(self.config.DATABASE_BACKUP_INTERVAL)
                    if self.running:
                        self.create_database_backup()
                except Exception as e:
                    self.logger.error(f"Errore backup database: {e}")
        
        self.backup_thread = threading.Thread(target=backup_worker, daemon=True)
        self.backup_thread.start()
        self.logger.info("Backup automatico database avviato")
    
    def create_database_backup(self):
        """Crea backup del database."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"netmaster_backup_{timestamp}.db"
            backup_path = os.path.join("backups", backup_name)
            
            # Copia database
            import shutil
            shutil.copy2(self.config.DATABASE_PATH, backup_path)
            
            self.logger.info(f"Backup database creato: {backup_path}")
            
            # Pulizia backup vecchi (mantieni ultimi 10)
            self.cleanup_old_backups()
            
        except Exception as e:
            self.logger.error(f"Errore creazione backup: {e}")
    
    def cleanup_old_backups(self):
        """Rimuove backup vecchi."""
        try:
            backup_dir = "backups"
            if not os.path.exists(backup_dir):
                return
            
            backups = [f for f in os.listdir(backup_dir) if f.startswith("netmaster_backup_")]
            backups.sort(reverse=True)  # Più recenti prima
            
            # Mantieni solo i 10 più recenti
            for old_backup in backups[10:]:
                old_path = os.path.join(backup_dir, old_backup)
                os.remove(old_path)
                self.logger.info(f"Backup vecchio rimosso: {old_backup}")
                
        except Exception as e:
            self.logger.error(f"Errore pulizia backup: {e}")
    
    def validate_environment(self):
        """Valida ambiente produzione."""
        self.logger.info("Validazione ambiente produzione...")
        
        # Verifica variabili d'ambiente
        required_vars = ['NETMASTER_USERNAME', 'NETMASTER_PASSWORD_HASH']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(f"Variabili d'ambiente mancanti: {', '.join(missing_vars)}")
        
        # Verifica database
        if not database.test_connection():
            raise ValueError("Connessione database fallita")
        
        # Verifica SSL se abilitato
        if self.config.USE_HTTPS:
            if not os.path.exists(self.config.SSL_CERT_PATH):
                raise ValueError(f"Certificato SSL non trovato: {self.config.SSL_CERT_PATH}")
            if not os.path.exists(self.config.SSL_KEY_PATH):
                raise ValueError(f"Chiave SSL non trovata: {self.config.SSL_KEY_PATH}")
        
        self.logger.info("✅ Ambiente produzione validato con successo")
    
    def start_server(self):
        """Avvia server in modalità produzione."""
        try:
            self.logger.info("🚀 AVVIO NETMASTER MONITORING SUITE - PRODUZIONE")
            self.logger.info(f"Host: {self.config.HOST}:{self.config.PORT}")
            self.logger.info(f"HTTPS: {'Abilitato' if self.config.USE_HTTPS else 'Disabilitato'}")
            self.logger.info(f"Database: {self.config.DATABASE_PATH}")
            
            # Validazione ambiente
            self.validate_environment()
            
            # Setup componenti produzione
            self.setup_signal_handlers()
            self.running = True
            self.setup_database_backup()
            
            # Configurazione Flask per produzione
            app.config['DEBUG'] = False
            app.config['TESTING'] = False
            
            # Avvio server
            if self.config.USE_HTTPS:
                # Server HTTPS
                ssl_context = (self.config.SSL_CERT_PATH, self.config.SSL_KEY_PATH)
                app.run(
                    host=self.config.HOST,
                    port=self.config.PORT,
                    ssl_context=ssl_context,
                    threaded=True
                )
            else:
                # Server HTTP
                app.run(
                    host=self.config.HOST,
                    port=self.config.PORT,
                    threaded=True
                )
                
        except Exception as e:
            self.logger.error(f"Errore avvio server: {e}", exc_info=True)
            self.shutdown()
            raise
    
    def shutdown(self):
        """Shutdown graceful del server."""
        self.logger.info("Avvio shutdown NetMaster...")
        self.running = False
        
        # Backup finale
        try:
            self.create_database_backup()
            self.logger.info("Backup finale completato")
        except Exception as e:
            self.logger.error(f"Errore backup finale: {e}")
        
        self.logger.info("✅ NetMaster arrestato correttamente")

def main():
    """Funzione principale."""
    print("🚀 NetMaster Monitoring Suite - Produzione")
    print("=" * 50)
    
    try:
        server = ProductionServer()
        server.start_server()
    except KeyboardInterrupt:
        print("\n⚠️ Interruzione utente")
    except Exception as e:
        print(f"❌ Errore fatale: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
