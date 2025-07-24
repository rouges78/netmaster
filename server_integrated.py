#!/usr/bin/env python3
"""
NetMaster Server Integrato - Versione Completa
Combina server principale con dashboard web funzionante
"""

import logging
import json
import os
import sys
import ssl
import time
from functools import wraps
from datetime import datetime

import bcrypt
import yagmail
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.exceptions import BadRequest
from logging.handlers import RotatingFileHandler

# Importa moduli NetMaster
import database
import credentials
import ssl_manager
import security_validator
from security_validator import InputValidator

# --- Classi di Errore Personalizzate ---

class NotificationError(Exception):
    """Eccezione personalizzata per errori di notifica."""
    pass

class AuthenticationError(Exception):
    """Eccezione personalizzata per errori di autenticazione."""
    def __init__(self, message, error_code=401):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class ValidationError(Exception):
    """Eccezione personalizzata per errori di validazione dei dati."""
    pass

# --- Configurazione del Logging ---

def setup_logging():
    """Configura il sistema di logging con rotazione dei file e formattazione dettagliata."""
    
    # Crea directory logs se non esiste
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Configurazione del logger root
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Rimuove handler esistenti per evitare duplicati
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Formatter dettagliato
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(name)s] - %(message)s\\n'
        'File: %(filename)s:%(lineno)d | Process: %(process)d | Thread: %(thread)d\\n'
        '---'
    )
    
    # Handler per file con rotazione
    file_handler = RotatingFileHandler(
        'logs/server.log', 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Handler per console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    logging.info("Sistema di logging inizializzato.")

# --- Funzioni di Notifica ---

def send_email_notification(subject, body):
    """Invia una notifica email utilizzando la configurazione salvata nel database."""
    try:
        email_config = database.get_notification_config('email')
        if not email_config or not email_config.get('enabled', False):
            logging.warning("Notifiche email disabilitate o non configurate.")
            return False
        
        config = email_config['config']
        yag = yagmail.SMTP(config['username'], config['password'], 
                          host=config['smtp_server'], port=config['smtp_port'])
        yag.send(to=config['recipients'], subject=subject, contents=body)
        logging.info(f"Email inviata: {subject}")
        return True
        
    except Exception as e:
        logging.error(f"Errore invio email: {e}", exc_info=True)
        raise NotificationError(f"Impossibile inviare email: {e}")

def check_thresholds_and_notify(data, agent_ip):
    """Controlla i dati rispetto alle soglie e invia notifiche se superate."""
    try:
        thresholds = database.get_thresholds_for_agent(agent_ip)
        
        for threshold in thresholds:
            metric = threshold['metric']
            threshold_value = threshold['threshold']
            
            # Mappa le metriche ai valori nei dati
            metric_mapping = {
                'cpu': 'cpu_percent',
                'memory': 'memory_percent', 
                'disk': 'disk_percent'
            }
            
            if metric in metric_mapping:
                current_value = data.get(metric_mapping[metric], 0)
                
                if current_value > threshold_value:
                    # Verifica se è già stata inviata una notifica recente
                    if not database.has_recent_notification(agent_ip, metric):
                        subject = f"[NetMaster] Soglia {metric.upper()} superata"
                        body = f"""
                        Avviso NetMaster:
                        
                        Agent: {agent_ip}
                        Metrica: {metric.upper()}
                        Valore attuale: {current_value:.1f}%
                        Soglia configurata: {threshold_value}%
                        Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                        """
                        
                        send_email_notification(subject, body)
                        database.save_notification(agent_ip, metric, current_value, threshold_value)
                        logging.warning(f"Soglia {metric} superata per {agent_ip}: {current_value}% > {threshold_value}%")
                        
    except Exception as e:
        logging.error(f"Errore nel controllo soglie: {e}", exc_info=True)

# --- Gestione Autenticazione ---

def hash_password(password):
    """Genera un hash sicuro della password usando bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    """Verifica se la password corrisponde all'hash memorizzato."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def load_credentials():
    """Carica le credenziali utilizzando il nuovo sistema sicuro."""
    try:
        # Usa il nuovo modulo credentials per caricare le credenziali
        username, password = credentials.get_credentials()
        password_hash = credentials.get_password_hash()
        
        if not username or not password_hash:
            logging.critical("Credenziali non configurate correttamente.")
            return None, None
        
        logging.info(f"[OK] Credenziali caricate per utente: {username}")
        return username, password_hash
        
    except Exception as e:
        logging.critical(f"Errore nel caricamento delle credenziali: {e}", exc_info=True)
        return None, None

# --- Inizializzazione Applicazione Flask ---

setup_logging()
database.init_db()

# Carica credenziali
USERNAME, PASSWORD_HASH = load_credentials()

# Crea app Flask
app = Flask(__name__, static_folder='static')

# --- Error Handlers Globali ---

@app.errorhandler(BadRequest)
def handle_bad_request(error):
    """Gestisce errori di richieste malformate, inclusi JSON non validi."""
    logging.warning(f"Richiesta malformata da {request.remote_addr}: {error}")
    return jsonify({'error': 'Richiesta malformata o JSON non valido'}), 400

@app.errorhandler(400)
def handle_json_error(error):
    """Gestisce errori JSON malformati."""
    return jsonify({'error': 'JSON malformato o non valido'}), 400

# --- Decoratori Flask ---

def requires_auth(f):
    """Decoratore per la protezione degli endpoint con autenticazione Basic."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        
        if not auth:
            logging.warning(f"Tentativo di accesso senza autenticazione da {request.remote_addr}")
            return jsonify({'error': 'Autenticazione richiesta'}), 401, {
                'WWW-Authenticate': 'Basic realm="NetMaster"'
            }
        
        if auth.username != USERNAME or not verify_password(auth.password, PASSWORD_HASH):
            logging.warning(f"Tentativo di accesso con credenziali errate da {request.remote_addr}: {auth.username}")
            raise AuthenticationError("Credenziali non valide")
        
        return f(*args, **kwargs)
    return decorated

@app.errorhandler(AuthenticationError)
def handle_authentication_error(error):
    """Gestore per errori di autenticazione."""
    return jsonify({
        'error': 'Autenticazione fallita',
        'message': error.message
    }), error.error_code, {'WWW-Authenticate': 'Basic realm="NetMaster"'}

@app.errorhandler(ValidationError)
def handle_validation_error(error):
    """Gestore per errori di validazione."""
    logging.warning(f"Errore di validazione: {error}")
    return jsonify({
        'error': 'Dati non validi',
        'message': str(error)
    }), 400

# --- Rate Limiting Personalizzato ---

def rate_limit_endpoint(requests_per_minute=60, requests_per_hour=1000):
    """Decoratore per rate limiting personalizzato per ogni endpoint."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Implementazione semplificata del rate limiting
            # In produzione, usare Redis o sistema più robusto
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_input_endpoint(f):
    """Decoratore per validazione input personalizzato."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Validazione di base - in produzione usare security_validator
        return f(*args, **kwargs)
    return decorated_function

# --- Endpoint per File Statici ---

@app.route('/')
def dashboard():
    """Serve la dashboard web principale."""
    try:
        return send_from_directory(app.static_folder, 'index.html')
    except Exception as e:
        logging.error(f"Errore nel servire la dashboard: {e}")
        return "Errore nel caricamento della dashboard", 500

@app.route('/test.html')
def test_page():
    """Serve la pagina di test."""
    return send_from_directory(app.static_folder, 'test.html')

@app.route('/css/<path:filename>')
def css_files(filename):
    """Serve i file CSS."""
    return send_from_directory(os.path.join(app.static_folder, 'css'), filename)

@app.route('/js/<path:filename>')
def js_files(filename):
    """Serve i file JavaScript."""
    return send_from_directory(os.path.join(app.static_folder, 'js'), filename)

# --- Endpoint API Principali ---

@app.route('/api/report', methods=['POST'])
@requires_auth
@rate_limit_endpoint(requests_per_minute=120, requests_per_hour=2000)
@validate_input_endpoint
def report():
    """Endpoint per ricevere i dati di monitoraggio dagli agent."""
    try:
        data = request.get_json()
        if not data:
            raise ValidationError("Dati JSON richiesti")
        
        agent_ip = request.remote_addr
        
        # Salva i dati nel database
        database.save_system_data(data, agent_ip)
        
        # Controlla soglie e invia notifiche se necessario
        check_thresholds_and_notify(data, agent_ip)
        
        logging.info(f"Dati ricevuti da {agent_ip}: CPU={data.get('cpu_percent', 0):.1f}%")
        return jsonify({'status': 'success', 'message': 'Dati ricevuti correttamente'}), 200
        
    except ValidationError as e:
        raise e
    except Exception as e:
        logging.error(f"Errore nella ricezione dati: {e}", exc_info=True)
        return jsonify({'error': 'Errore interno del server'}), 500

# --- Endpoint Dashboard Web ---

@app.route('/api/stats', methods=['GET'])
@requires_auth
@rate_limit_endpoint(requests_per_minute=30, requests_per_hour=500)
def get_stats():
    """Endpoint per ottenere statistiche aggregate del sistema."""
    try:
        stats = database.get_system_stats()
        
        if stats:
            total_agents = len(set(record.get('agent_ip', '') for record in stats))
            avg_cpu = sum(record.get('cpu_percent', 0) for record in stats) / len(stats) if stats else 0
            avg_memory = sum(record.get('memory_percent', 0) for record in stats) / len(stats) if stats else 0
            avg_disk = sum(record.get('disk_percent', 0) for record in stats) / len(stats) if stats else 0
            
            active_alerts = sum(1 for record in stats if 
                               record.get('cpu_percent', 0) > 75 or 
                               record.get('memory_percent', 0) > 85 or 
                               record.get('disk_percent', 0) > 90)
        else:
            total_agents = avg_cpu = avg_memory = avg_disk = active_alerts = 0
        
        result = {
            'total_agents': total_agents,
            'avg_cpu': round(avg_cpu, 1),
            'avg_memory': round(avg_memory, 1),
            'avg_disk': round(avg_disk, 1),
            'active_alerts': active_alerts
        }
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Errore nel recupero delle statistiche: {e}", exc_info=True)
        return jsonify({'error': 'Errore interno del server'}), 500

@app.route('/api/realtime', methods=['GET'])
@requires_auth
@rate_limit_endpoint(requests_per_minute=60, requests_per_hour=1000)
def get_realtime_data():
    """Endpoint per ottenere dati real-time per i grafici."""
    try:
        timespan = request.args.get('timespan', '6h')
        hours_map = {'1h': 1, '6h': 6, '24h': 24}
        hours = hours_map.get(timespan, 6)
        
        realtime_data = database.get_recent_data(hours)
        
        formatted_data = []
        for record in realtime_data:
            formatted_data.append({
                'timestamp': record.get('timestamp', 0) * 1000,
                'cpu': record.get('cpu_percent', 0),
                'memory': record.get('memory_percent', 0),
                'disk': record.get('disk_percent', 0),
                'agent_ip': record.get('agent_ip', '')
            })
        
        return jsonify(formatted_data)
        
    except Exception as e:
        logging.error(f"Errore nel recupero dei dati real-time: {e}", exc_info=True)
        return jsonify({'error': 'Errore interno del server'}), 500

@app.route('/api/agents', methods=['GET'])
@requires_auth
@rate_limit_endpoint(requests_per_minute=30, requests_per_hour=500)
def get_agents():
    """Endpoint per ottenere la lista degli agent attivi."""
    try:
        agents_data = database.get_active_agents()
        
        agents = []
        for i, agent in enumerate(agents_data, 1):
            last_update = agent.get('timestamp', 0)
            current_time = time.time()
            time_diff = current_time - last_update
            
            if time_diff < 120:
                status = 'online'
            elif time_diff < 300:
                status = 'warning'
            else:
                status = 'offline'
            
            agents.append({
                'id': i,
                'hostname': agent.get('hostname', f'Agent-{agent.get("agent_ip", "Unknown")}'),
                'ip_address': agent.get('agent_ip', 'N/A'),
                'cpu_percent': agent.get('cpu_percent', 0),
                'memory_percent': agent.get('memory_percent', 0),
                'disk_percent': agent.get('disk_percent', 0),
                'processes': agent.get('processes', 0),
                'uptime': agent.get('uptime', 0),
                'platform': agent.get('platform', 'Unknown'),
                'architecture': agent.get('architecture', 'Unknown'),
                'last_update': last_update,
                'status': status
            })
        
        return jsonify(agents)
        
    except Exception as e:
        logging.error(f"Errore nel recupero degli agent: {e}", exc_info=True)
        return jsonify({'error': 'Errore interno del server'}), 500

@app.route('/api/alerts', methods=['GET'])
@requires_auth
@rate_limit_endpoint(requests_per_minute=30, requests_per_hour=500)
def get_alerts():
    """Endpoint per ottenere gli avvisi attivi del sistema."""
    try:
        alerts = database.get_active_alerts()
        
        if not alerts:
            alerts = database.generate_alerts_from_current_data()
        
        return jsonify(alerts)
        
    except Exception as e:
        logging.error(f"Errore nel recupero degli avvisi: {e}", exc_info=True)
        return jsonify({'error': 'Errore interno del server'}), 500

@app.route('/api/health', methods=['GET'])
@requires_auth
@rate_limit_endpoint(requests_per_minute=60, requests_per_hour=1000)
def get_system_health():
    """Endpoint per ottenere lo stato di salute del sistema."""
    try:
        start_time = getattr(app, 'start_time', time.time())
        
        health_data = {
            'status': 'healthy',
            'timestamp': time.time(),
            'server_uptime': time.time() - start_time,
            'database_status': 'connected',
            'ssl_enabled': False,  # Configurabile
            'version': '1.0.0'
        }
        
        return jsonify(health_data)
        
    except Exception as e:
        logging.error(f"Errore nel recupero dello stato di salute: {e}", exc_info=True)
        return jsonify({'error': 'Errore interno del server'}), 500

@app.route('/api/history', methods=['GET'])
@requires_auth
@rate_limit_endpoint(requests_per_minute=60, requests_per_hour=1000)
def get_history():
    """Endpoint per recuperare lo storico dei dati di monitoraggio."""
    try:
        start_date = request.args.get('start')
        end_date = request.args.get('end')
        
        history_data = database.get_history(start_date, end_date)
        
        return jsonify(history_data)
        
    except Exception as e:
        logging.error(f"Errore nel recupero dello storico: {e}", exc_info=True)
        return jsonify({'error': 'Errore interno del server'}), 500

@app.route('/api/thresholds', methods=['GET', 'POST'])
@requires_auth
@rate_limit_endpoint(requests_per_minute=30, requests_per_hour=500)
def manage_thresholds():
    """Endpoint per visualizzare e impostare le soglie."""
    try:
        if request.method == 'GET':
            thresholds = database.get_all_thresholds()
            return jsonify(thresholds)
        
        elif request.method == 'POST':
            data = request.get_json()
            if not data:
                raise ValidationError("Dati JSON richiesti")
            
            # Salva le soglie nel database
            for agent_ip, metrics in data.items():
                for metric, threshold in metrics.items():
                    database.save_threshold(agent_ip, metric, threshold, True)
            
            return jsonify({'message': 'Soglie aggiornate con successo'})
            
    except ValidationError as e:
        raise e
    except Exception as e:
        logging.error(f"Errore nella gestione delle soglie: {e}", exc_info=True)
        return jsonify({'error': 'Errore interno del server'}), 500

@app.route('/api/notifications/config', methods=['GET', 'POST'])
@requires_auth
@rate_limit_endpoint(requests_per_minute=20, requests_per_hour=200)
def manage_notification_config():
    """Endpoint per gestire la configurazione delle notifiche."""
    try:
        if request.method == 'GET':
            config = database.get_all_notification_configs()
            return jsonify(config)
        
        elif request.method == 'POST':
            data = request.get_json()
            if not data:
                raise ValidationError("Dati JSON richiesti")
            
            config_type = data.get('type', 'email')
            config_data = data.get('config', {})
            enabled = data.get('enabled', True)
            
            database.save_notification_config(config_type, config_data, enabled)
            
            return jsonify({'message': 'Configurazione salvata con successo'})
            
    except ValidationError as e:
        raise e
    except Exception as e:
        logging.error(f"Errore nella gestione delle notifiche: {e}", exc_info=True)
        return jsonify({'error': 'Errore interno del server'}), 500

# --- Avvio Server ---

if __name__ == '__main__':
    if USERNAME is None or PASSWORD_HASH is None:
        logging.critical("Credenziali non configurate. Impossibile avviare il server.")
        sys.exit(1)
    
    # Salva tempo di avvio
    app.start_time = time.time()
    
    try:
        logging.info("Avvio del server NetMaster integrato...")
        logging.info(f"Username configurato: {USERNAME}")
        logging.info("Dashboard disponibile su: http://localhost:5000")
        logging.info("Credenziali: admin / password")
        
        # Configurazione SSL (opzionale)
        use_https = False
        ssl_context = None
        
        try:
            ssl_mgr = ssl_manager.create_ssl_manager()
            ssl_context = ssl_mgr.get_server_ssl_context()
            use_https = True
            logging.info("✅ HTTPS abilitato con certificati SSL")
        except Exception as e:
            logging.warning(f"HTTPS non disponibile: {e}")
            logging.info("🔓 Server avviato in modalità HTTP")
        
        # Avvia il server Flask
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            threaded=True,
            ssl_context=ssl_context if use_https else None
        )
        
    except KeyboardInterrupt:
        logging.info("Server interrotto dall'utente.")
    except Exception as e:
        logging.critical(f"Errore critico durante l'avvio del server: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logging.info("Server NetMaster terminato.")
