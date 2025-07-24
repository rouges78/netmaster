import requests
import json
import time
import platform
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

# Importa il nuovo modulo per la gestione sicura delle credenziali
import credentials
# Importa il nuovo modulo per la gestione SSL/TLS
import ssl_manager

# Importa psutil solo se disponibile
try:
    import psutil
except ImportError:
    print("Errore: il modulo 'psutil' non è installato. Eseguire 'pip install psutil'")
    sys.exit(1)

# --- Configurazione del Logging ---

def setup_agent_logging():
    """Configura il logging per l'agent."""
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [AGENT] - %(message)s'
    )

    # Handler per il file di log dell'agent
    agent_handler = RotatingFileHandler(
        os.path.join(log_dir, 'agent.log'), maxBytes=5*1024*1024, backupCount=3
    )
    agent_handler.setFormatter(formatter)
    agent_handler.setLevel(logging.INFO)

    # Handler per la console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # Configura il logger
    logger = logging.getLogger('agent')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(agent_handler)
    logger.addHandler(console_handler)
    return logger

logger = setup_agent_logging()

# --- Classe di Errore Personalizzata ---

class AgentError(Exception):
    """Eccezione personalizzata per errori specifici dell'agent."""
    def __init__(self, message, error_code=None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

# --- Funzioni di Raccolta Dati ---

def get_system_info():
    """Raccoglie le informazioni di base sul sistema."""
    try:
        return {
            "cpu_usage": psutil.cpu_percent(interval=1),
            "memory": psutil.virtual_memory().percent,
            "disk": psutil.disk_usage('/').percent,
            "system": platform.system(),
            "node": platform.node(),
            "release": platform.release(),
            "version": platform.version(),
        }
    except Exception as e:
        raise AgentError(f"Errore critico durante la raccolta dati di sistema: {e}")

# --- Funzioni di Configurazione e Comunicazione ---

def load_config():
    """
    Carica e valida la configurazione utilizzando il nuovo sistema sicuro.
    Le credenziali vengono caricate dalle variabili d'ambiente o file .env.
    """
    try:
        # Carica configurazione base da config.json (senza credenziali)
        config = {}
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            logger.warning("⚠️  File config.json non trovato, uso configurazione di default")
        except json.JSONDecodeError:
            raise AgentError("❌ Errore di formato nel file config.json.")
        
        # Carica credenziali dal sistema sicuro
        username, password = credentials.get_credentials()
        if not username or not password:
            raise AgentError("❌ Credenziali non configurate. Configura NETMASTER_USERNAME e NETMASTER_PASSWORD")
        
        # Configurazione finale con valori di default
        # Usa HTTPS per default per maggiore sicurezza
        default_url = config.get('server_url', 'https://localhost:5000/api/report')
        final_config = {
            'server_url': default_url,
            'collection_interval': config.get('collection_interval', 60),
            'username': username,
            'password': password,
            'verify_ssl': config.get('verify_ssl', False)  # False per certificati auto-firmati
        }
        
        # Validazione
        if not isinstance(final_config['collection_interval'], int) or final_config['collection_interval'] < 10:
            raise AgentError("L'intervallo di raccolta deve essere un numero intero >= 10.")
        
        logger.info(f"✅ Configurazione caricata per utente: {username}")
        logger.info(f"🌐 Server URL: {final_config['server_url']}")
        logger.info(f"⏱️  Intervallo raccolta: {final_config['collection_interval']}s")
        
        return final_config

    except AgentError as e:
        raise e # Rilancia l'eccezione specifica
    except Exception as e:
        raise AgentError(f"❌ Errore imprevisto nel caricamento della configurazione: {e}")


def send_data_to_server(data, config):
    """
    Invia i dati al server utilizzando l'autenticazione Basic con supporto HTTPS.
    Gestisce certificati auto-firmati per sviluppo e certificati validi per produzione.
    """
    try:
        # Determina se usare HTTPS
        is_https = config['server_url'].startswith('https://')
        verify_ssl = config.get('verify_ssl', False)
        
        # Configurazione SSL per HTTPS
        ssl_context = None
        if is_https:
            try:
                ssl_mgr = ssl_manager.create_ssl_manager()
                ssl_context = ssl_mgr.get_client_ssl_context(verify_cert=verify_ssl)
                logger.info(f"[HTTPS] Connessione sicura a {config['server_url']}")
                if not verify_ssl:
                    logger.info("[HTTPS] Certificati auto-firmati accettati (sviluppo)")
            except Exception as e:
                logger.warning(f"[HTTPS] Errore configurazione SSL: {e}")
                # Fallback: disabilita verifica SSL per certificati auto-firmati
                verify_ssl = False
        
        # Configurazione della sessione requests
        session = requests.Session()
        if is_https:
            session.verify = verify_ssl
            if not verify_ssl:
                # Disabilita warning per certificati non verificati
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Invio dati al server
        response = session.post(
            config['server_url'],
            json=data,
            auth=(config['username'], config['password']),
            headers={'Content-Type': 'application/json'},
            timeout=15
        )

        if response.status_code == 200:
            protocol = "HTTPS" if is_https else "HTTP"
            logger.info(f"[{protocol}] Dati inviati con successo a {config['server_url']}")
            return True
        elif response.status_code == 401:
            raise AgentError("[AUTH] Autenticazione fallita (401). Controllare username e password.", error_code=401)
        else:
            raise AgentError(f"[SERVER] Errore dal server: {response.status_code} - {response.text}", error_code=response.status_code)

    except requests.exceptions.SSLError as e:
        logger.error(f"[SSL] Errore SSL: {e}")
        if "certificate verify failed" in str(e).lower():
            raise AgentError("[SSL] Certificato server non valido. Configura 'verify_ssl': false per certificati auto-firmati.")
        else:
            raise AgentError(f"[SSL] Errore SSL: {e}")
    except requests.exceptions.Timeout:
        raise AgentError("[NETWORK] Timeout durante la connessione al server.")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"[NETWORK] Errore connessione: {e}")
        if is_https and "SSL" in str(e):
            raise AgentError("[HTTPS] Impossibile stabilire connessione SSL. Verifica che il server supporti HTTPS.")
        else:
            raise AgentError("[NETWORK] Impossibile connettersi al server. Controllare l'URL e la connettività.")
    except Exception as e:
        raise AgentError(f"[ERROR] Errore imprevisto durante l'invio dei dati: {e}")

# --- Ciclo Principale dell'Agent ---

def run_agent():
    """
    Funzione principale che gestisce il ciclo di vita dell'agent.
    """
    try:
        config = load_config()
        logger.info("Agent avviato. Configurazione caricata correttamente.")
    except AgentError as e:
        logger.critical(f"Errore fatale all'avvio: {e.message}")
        sys.exit(1)

    consecutive_errors = 0
    max_consecutive_errors = 5

    while True:
        try:
            system_info = get_system_info()
            send_data_to_server(system_info, config)
            consecutive_errors = 0  # Reset su successo
            time.sleep(config['collection_interval'])

        except AgentError as e:
            consecutive_errors += 1
            logger.error(f"Errore (tentativo {consecutive_errors}/{max_consecutive_errors}): {e.message}")

            if e.error_code == 401:
                logger.critical("Errore di autenticazione. L'agent verrà arrestato.")
                break # Esce dal ciclo in caso di errore di autenticazione

            if consecutive_errors >= max_consecutive_errors:
                logger.critical("Raggiunto il numero massimo di errori consecutivi. L'agent si arresta.")
                break

            # Calcolo del ritardo con backoff esponenziale
            retry_delay = min(300, config['collection_interval'] * (2 ** (consecutive_errors - 1)))
            logger.info(f"Prossimo tentativo tra {retry_delay:.1f} secondi.")
            time.sleep(retry_delay)

        except KeyboardInterrupt:
            logger.info("Arresto dell'agent richiesto dall'utente.")
            break
        except Exception as e:
            logger.critical(f"Errore non gestito nel ciclo principale: {e}", exc_info=True)
            break

    logger.info("Agent terminato.")


if __name__ == "__main__":
    run_agent()
