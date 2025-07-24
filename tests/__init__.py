"""
NetMaster Test Suite
Configurazione e utilities per i test automatizzati
"""

import os
import sys
import logging

# Configurazione logging per test
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Configurazione test
TEST_CONFIG = {
    'server_host': '127.0.0.1',
    'api_port': 5001,
    'integration_port': 5002,
    'timeout': 30,
    'auth': ('admin', 'password'),
    'test_data_retention_days': 1
}

# Utilities per test
def get_test_config():
    """Restituisce la configurazione per i test"""
    return TEST_CONFIG.copy()

def cleanup_test_data():
    """Pulisce i dati di test dal database"""
    try:
        import database
        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        # Rimuovi dati di test
        test_hostnames = [
            'TEST-PC-INTEGRATION',
            'TEST-PERSISTENCE', 
            'LOAD-TEST-%',
            'CYCLE-TEST-PC'
        ]
        
        for hostname in test_hostnames:
            if '%' in hostname:
                cursor.execute("DELETE FROM system_data WHERE hostname LIKE ?", (hostname,))
            else:
                cursor.execute("DELETE FROM system_data WHERE hostname = ?", (hostname,))
        
        conn.commit()
        conn.close()
        
        print("[CLEAN] Dati di test puliti dal database")
        
    except Exception as e:
        print(f"[WARNING] Errore pulizia dati test: {e}")

print("[INIT] NetMaster Test Suite inizializzata")
