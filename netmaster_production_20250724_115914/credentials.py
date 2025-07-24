"""
Modulo per la gestione sicura delle credenziali.
Utilizza variabili d'ambiente con fallback per compatibilità.
"""

import os
import json
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

class CredentialsError(Exception):
    """Eccezione per errori di gestione credenziali."""
    pass

def load_from_env_file(env_file: str = '.env') -> dict:
    """
    Carica le variabili d'ambiente da un file .env se presente.
    
    Args:
        env_file: Percorso del file .env
        
    Returns:
        dict: Dizionario con le variabili caricate
    """
    env_vars = {}
    if os.path.exists(env_file):
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # Rimuovi virgolette se presenti
                        value = value.strip('"\'')
                        env_vars[key.strip()] = value
                        # Imposta anche come variabile d'ambiente per questa sessione
                        os.environ[key.strip()] = value
            logger.info(f"Caricate {len(env_vars)} variabili da {env_file}")
        except Exception as e:
            logger.warning(f"Errore nel caricamento di {env_file}: {e}")
    return env_vars

def get_credentials() -> Tuple[Optional[str], Optional[str]]:
    """
    Ottiene le credenziali in modo sicuro.
    
    Priorità:
    1. Variabili d'ambiente NETMASTER_USERNAME e NETMASTER_PASSWORD
    2. File .env locale
    3. Fallback su config.json (deprecato, con warning)
    
    Returns:
        Tuple[username, password]: Le credenziali o (None, None) se non trovate
    """
    # Carica prima il file .env se presente
    load_from_env_file()
    
    # Prova a ottenere dalle variabili d'ambiente
    username = os.getenv('NETMASTER_USERNAME')
    password = os.getenv('NETMASTER_PASSWORD')
    
    if username and password:
        logger.info("Credenziali caricate dalle variabili d'ambiente")
        return username, password
    
    # Fallback su config.json (deprecato)
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            
        username = config.get('username')
        password = config.get('password')
        
        if username and password:
            logger.warning("[DEPRECATO] Credenziali caricate da config.json. "
                         "Usa variabili d'ambiente per maggiore sicurezza!")
            return username, password
            
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        pass
    
    logger.error("[ERRORE] Credenziali non trovate. Configura NETMASTER_USERNAME e NETMASTER_PASSWORD")
    return None, None

def get_password_hash() -> Optional[str]:
    """
    Ottiene l'hash della password per il server.
    
    Returns:
        str: Hash della password o None se non trovato
    """
    # Prova prima dalle variabili d'ambiente
    password_hash = os.getenv('NETMASTER_PASSWORD_HASH')
    if password_hash:
        logger.info("Hash password caricato dalle variabili d'ambiente")
        return password_hash
    
    # Fallback su config.json
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        password_hash = config.get('password_hash')
        if password_hash:
            logger.warning("[DEPRECATO] Hash password caricato da config.json")
            return password_hash
            
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        pass
    
    logger.error("Hash password non trovato")
    return None

def create_env_template():
    """
    Crea un file .env.template con le variabili necessarie.
    """
    template_content = """# NetMaster Monitoring Suite - Configurazione Credenziali
# Copia questo file in '.env' e inserisci le tue credenziali

# Credenziali per autenticazione (OBBLIGATORIO)
NETMASTER_USERNAME=admin
NETMASTER_PASSWORD=your_secure_password_here

# Hash della password per il server (generato automaticamente se non presente)
# NETMASTER_PASSWORD_HASH=

# Configurazioni opzionali
# NETMASTER_SERVER_HOST=localhost
# NETMASTER_SERVER_PORT=5000
# NETMASTER_COLLECTION_INTERVAL=60
"""
    
    try:
        with open('.env.template', 'w', encoding='utf-8') as f:
            f.write(template_content)
        logger.info("Creato file .env.template")
    except Exception as e:
        logger.error(f"Errore nella creazione di .env.template: {e}")

def validate_credentials() -> bool:
    """
    Valida che le credenziali siano configurate correttamente.
    
    Returns:
        bool: True se le credenziali sono valide
    """
    username, password = get_credentials()
    
    if not username or not password:
        logger.error("[ERRORE] Credenziali mancanti!")
        logger.info("[INFO] Per configurare le credenziali:")
        logger.info("   1. Crea un file .env nella directory del progetto")
        logger.info("   2. Aggiungi: NETMASTER_USERNAME=admin")
        logger.info("   3. Aggiungi: NETMASTER_PASSWORD=tua_password_sicura")
        logger.info("   4. Oppure imposta le variabili d'ambiente del sistema")
        return False
    
    if len(password) < 8:
        logger.warning("[ATTENZIONE] Password troppo corta. Consigliata lunghezza minima: 8 caratteri")
    
    logger.info("[OK] Credenziali configurate correttamente")
    return True

if __name__ == "__main__":
    # Test del modulo
    logging.basicConfig(level=logging.INFO)
    
    print("[NETMASTER] Test del sistema di credenziali")
    print("-" * 50)
    
    # Crea template se non esiste
    if not os.path.exists('.env.template'):
        create_env_template()
        print("[OK] Creato .env.template")
    
    # Valida credenziali
    if validate_credentials():
        username, password = get_credentials()
        print(f"[INFO] Username: {username}")
        print(f"[INFO] Password: {'*' * len(password) if password else 'NON CONFIGURATA'}")
        
        password_hash = get_password_hash()
        print(f"[INFO] Hash: {'Presente' if password_hash else 'Non trovato'}")
    else:
        print("[ERRORE] Configurazione credenziali non valida")
