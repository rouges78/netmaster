# c:\Users\davide\Desktop\progetto-server\server.py

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
from flask import Flask, request, jsonify, make_response
from logging.handlers import RotatingFileHandler

# Importa il nuovo modulo per la gestione del database
import database
# Importa il nuovo modulo per la gestione sicura delle credenziali
import credentials
# Importa il nuovo modulo per la gestione SSL/TLS
import ssl_manager
# Importa il nuovo modulo per la validazione e sicurezza
import security_validator
from security_validator import rate_limit, validate_input, InputValidator

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
    """
    Configura il sistema di logging con rotazione dei file e formattazione dettagliata.
    """
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(name)s] - %(message)s\n'
        'File: %(filename)s:%(lineno)d | Process: %(process)d | Thread: %(thread)d\n---'
    )

    # Handler per il file di log principale
    main_handler = RotatingFileHandler(
        os.path.join(log_dir, 'server.log'), maxBytes=10*1024*1024, backupCount=5
    )
    main_handler.setFormatter(formatter)
    main_handler.setLevel(logging.INFO)

    # Handler per gli errori
    error_handler = RotatingFileHandler(
        os.path.join(log_dir, 'error.log'), maxBytes=10*1024*1024, backupCount=5
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)

    # Handler per la console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)

    # Configura il logger root
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(main_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(console_handler)

    logging.info("Sistema di logging inizializzato.")

# --- Funzioni di Notifica ---

def send_email_notification(subject, body):
    """
    Invia una notifica email utilizzando la configurazione salvata nel database.
    """
    try:
        email_config = database.get_notification_config('email')
        if not email_config or not email_config.get('enabled'):
            logging.warning("Invio email saltato: configurazione non trovata o disabilitata.")
            return False

        config = email_config['config']
        yag = yagmail.SMTP(config['username'], config['password'])
        yag.send(to=config['to_email'], subject=subject, contents=body)
        logging.info(f"Email di notifica inviata a {config['to_email']}.")
        return True
    except Exception as e:
        logging.error(f"Errore critico durante l'invio dell'email: {e}", exc_info=True)
        raise NotificationError(f"Impossibile inviare l'email: {e}")

def check_thresholds_and_notify(data, agent_ip):
    """
    Controlla i dati rispetto alle soglie e invia notifiche se superate.
    Utilizza le funzioni del modulo database.
    """
    try:
        thresholds = database.get_thresholds_for_agent(agent_ip)
        if not thresholds:
            return

        for metric, threshold_value, enabled in thresholds:
            if not enabled:
                continue

            if metric in data and data[metric] > threshold_value:
                if not database.has_recent_notification(agent_ip, metric, hours=1):
                    logging.warning(
                        f"Soglia superata per {agent_ip} sulla metrica '{metric}'. "
                        f"Valore: {data[metric]}, Soglia: {threshold_value}"
                    )
                    
                    # Salva la notifica nel DB
                    database.save_notification(
                        agent_ip=agent_ip,
                        metric=metric,
                        value=data[metric],
                        threshold=threshold_value,
                        status='sent'
                    )

                    # Invia la notifica email
                    subject = f"Allarme NetMaster: Soglia superata per {agent_ip}"
                    body = (
                        f"L'agent {agent_ip} ha superato la soglia per la metrica '{metric}'.\n"
                        f"Valore attuale: {data[metric]}%\n"
                        f"Soglia impostata: {threshold_value}%\n"
                        f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    send_email_notification(subject, body)

    except Exception as e:
        logging.error(f"Errore durante il controllo delle soglie per {agent_ip}: {e}", exc_info=True)


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
        # Utilizza il nuovo sistema di credenziali sicuro
        username, password = credentials.get_credentials()
        
        if not username or not password:
            logging.critical("❌ Credenziali non configurate. Usa variabili d'ambiente o file .env")
            logging.info("💡 Configura NETMASTER_USERNAME e NETMASTER_PASSWORD")
            return None, None
        
        # Ottieni l'hash della password
        password_hash = credentials.get_password_hash()
        
        # Se l'hash non è presente, generalo dalla password
        if not password_hash:
            logging.info("🔐 Generazione hash password...")
            password_hash = hash_password(password)
            logging.info("✅ Hash password generato. Considera di salvarlo in NETMASTER_PASSWORD_HASH")
        
        logging.info(f"✅ Credenziali caricate per utente: {username}")
        return username, password_hash
        
    except Exception as e:
        logging.critical(f"❌ Errore nel caricamento delle credenziali: {e}", exc_info=True)
        return None, None

# --- Inizializzazione Applicazione Flask ---

setup_logging()
database.init_db()  # Inizializza il database all'avvio

app = Flask(__name__)
USERNAME, PASSWORD_HASH = load_credentials()

# --- Decoratori e Gestori di Errori ---

def requires_auth(f):
    """Decoratore per la protezione degli endpoint con autenticazione Basic."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if USERNAME is None or PASSWORD_HASH is None:
            return handle_authentication_error(AuthenticationError("Configurazione server non valida.", 500))
        
        auth = request.authorization
        if not auth or not auth.username or not auth.password:
            return handle_authentication_error(AuthenticationError("Credenziali di autenticazione richieste."))
        
        if auth.username != USERNAME or not verify_password(auth.password, PASSWORD_HASH):
            logging.warning(f"Tentativo di accesso fallito per l'utente: {auth.username}")
            return handle_authentication_error(AuthenticationError("Credenziali non valide."))
        
        logging.info(f"Accesso autorizzato per l'utente: {auth.username}")
        return f(*args, **kwargs)
    return decorated

@app.errorhandler(AuthenticationError)
def handle_authentication_error(error):
    """Gestore per errori di autenticazione."""
    response = jsonify({'error': 'Autenticazione fallita', 'message': error.message})
    response.status_code = error.error_code
    if error.error_code == 401:
        response.headers['WWW-Authenticate'] = 'Basic realm="Login Required"'
    return response

@app.errorhandler(ValidationError)
def handle_validation_error(error):
    """Gestore per errori di validazione."""
    logging.warning(f"Dati non validi ricevuti: {error.message}")
    response = jsonify({'error': 'Dati non validi', 'message': error.message})
    response.status_code = 400
    return response

# --- Funzioni di Validazione ---

def validate_system_data(data):
    """Valida i dati di sistema ricevuti dall'agent."""
    required_fields = ['cpu_usage', 'memory', 'disk', 'system', 'node', 'release', 'version']
    for field in required_fields:
        if field not in data:
            raise ValidationError(f"Campo richiesto mancante: '{field}'")
    
    for field in ['cpu_usage', 'memory', 'disk']:
        value = data[field]
        if not isinstance(value, (int, float)) or not (0 <= value <= 100):
            raise ValidationError(f"Il campo '{field}' deve essere un numero tra 0 e 100.")

# --- Endpoint API ---

@app.route('/api/report', methods=['POST'])
@requires_auth
@rate_limit(requests_per_minute=120, requests_per_hour=2000)  # Limiti generosi per agent legittimi
@validate_input(InputValidator.validate_system_data)
def report():
    """Endpoint per ricevere i dati di monitoraggio dagli agent con validazione rigorosa."""
    agent_ip = request.remote_addr
    
    # I dati sono già stati validati dal decoratore @validate_input
    data = g.validated_data
    
    try:
        # Salva i dati validati nel database
        database.save_system_data(data, agent_ip)
        logging.info(f"[REPORT] Dati validati ricevuti e salvati da agent {agent_ip} (hostname: {data.get('hostname', 'unknown')})")
        
        # Log delle metriche per monitoraggio
        logging.debug(f"[METRICS] {agent_ip}: CPU={data['cpu_percent']}%, RAM={data['memory_percent']}%, DISK={data['disk_percent']}%")
        
        # Controlla le soglie e invia notifiche se necessario
        check_thresholds_and_notify(data, agent_ip)
        
        return jsonify({
            "status": "success", 
            "message": "Dati ricevuti e validati correttamente.",
            "timestamp": data['timestamp'],
            "hostname": data['hostname']
        }), 200
        
    except Exception as e:
        logging.error(f"[ERROR] Errore durante l'elaborazione dei dati da {agent_ip}: {e}", exc_info=True)
        security_validator.log_security_event("DATA_PROCESSING_ERROR", f"Errore elaborazione dati: {e}", "ERROR")
        return jsonify({
            "status": "error", 
            "message": "Errore interno del server."
        }), 500

@app.route('/api/thresholds', methods=['GET', 'POST'])
@requires_auth
@rate_limit(requests_per_minute=30, requests_per_hour=500)  # Limiti più restrittivi per configurazione
def manage_thresholds():
    """Endpoint per visualizzare e impostare le soglie."""
    if request.method == 'POST':
        try:
            data = request.get_json()
            required = ['agent_ip', 'metric', 'threshold', 'enabled']
            if not all(k in data for k in required):
                return jsonify({'error': 'Dati incompleti'}), 400
            
            database.save_threshold(
                data['agent_ip'], data['metric'], data['threshold'], data['enabled']
            )
            return jsonify({'status': 'success', 'message': 'Soglia salvata'}), 201
        except Exception as e:
            logging.error(f"Errore salvataggio soglia: {e}", exc_info=True)
            return jsonify({'error': 'Errore interno del server'}), 500
    else: # GET
        try:
            all_thresholds = database.get_all_thresholds()
            return jsonify(all_thresholds), 200
        except Exception as e:
            logging.error(f"Errore recupero soglie: {e}", exc_info=True)
            return jsonify({'error': 'Errore interno del server'}), 500

@app.route('/api/notifications/config', methods=['GET', 'POST'])
@requires_auth
@rate_limit(requests_per_minute=20, requests_per_hour=200)  # Limiti restrittivi per notifiche
def manage_notification_config():
    """Endpoint per gestire la configurazione delle notifiche."""
    if request.method == 'POST':
        try:
            data = request.get_json()
            required = ['type', 'config', 'enabled']
            if not all(k in data for k in required):
                return jsonify({'error': 'Dati incompleti'}), 400

            database.save_notification_config(data['type'], data['config'], data['enabled'])
            return jsonify({'status': 'success', 'message': 'Configurazione notifiche salvata'}), 201
        except Exception as e:
            logging.error(f"Errore salvataggio config notifiche: {e}", exc_info=True)
            return jsonify({'error': 'Errore interno del server'}), 500
    else: # GET
        try:
            all_configs = database.get_all_notification_configs()
            return jsonify(all_configs), 200
        except Exception as e:
            logging.error(f"Errore recupero config notifiche: {e}", exc_info=True)
            return jsonify({'error': 'Errore interno del server'}), 500

@app.route('/api/history', methods=['GET'])
@requires_auth
@validate_input
@rate_limit(requests_per_minute=60, requests_per_hour=1000)
def get_history():
    """
    Endpoint per recuperare lo storico dei dati di monitoraggio.
    """
    try:
        start_date = request.args.get('start')
        end_date = request.args.get('end')
        
        history_data = database.get_history(start_date, end_date)
        
        logging.info(f"Recuperato storico dati: {len(history_data)} record")
        return jsonify(history_data)
        
    except Exception as e:
        logging.error(f"Errore nel recupero dello storico: {e}", exc_info=True)
        return jsonify({'error': 'Errore interno del server'}), 500


# --- Nuovi Endpoint per Dashboard Web ---

@app.route('/api/stats', methods=['GET'])
@requires_auth
@validate_input
@rate_limit(requests_per_minute=30, requests_per_hour=500)
def get_stats():
    """
    Endpoint per ottenere statistiche aggregate del sistema.
    """
    try:
        stats = database.get_system_stats()
        
        # Calcola statistiche aggregate
        if stats:
            total_agents = len(set(record.get('agent_ip', '') for record in stats))
            avg_cpu = sum(record.get('cpu_percent', 0) for record in stats) / len(stats) if stats else 0
            avg_memory = sum(record.get('memory_percent', 0) for record in stats) / len(stats) if stats else 0
            avg_disk = sum(record.get('disk_percent', 0) for record in stats) / len(stats) if stats else 0
            
            # Conta avvisi attivi (simulato per ora)
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
        
        logging.info(f"Statistiche sistema recuperate: {result}")
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Errore nel recupero delle statistiche: {e}", exc_info=True)
        return jsonify({'error': 'Errore interno del server'}), 500


@app.route('/api/realtime', methods=['GET'])
@requires_auth
@validate_input
@rate_limit(requests_per_minute=60, requests_per_hour=1000)
def get_realtime_data():
    """
    Endpoint per ottenere dati real-time per i grafici.
    """
    try:
        timespan = request.args.get('timespan', '6h')
        
        # Converte timespan in ore
        hours_map = {'1h': 1, '6h': 6, '24h': 24}
        hours = hours_map.get(timespan, 6)
        
        # Recupera dati recenti
        realtime_data = database.get_recent_data(hours)
        
        # Formatta i dati per i grafici
        formatted_data = []
        for record in realtime_data:
            formatted_data.append({
                'timestamp': record.get('timestamp', 0) * 1000,  # Converti in millisecondi per JS
                'cpu': record.get('cpu_percent', 0),
                'memory': record.get('memory_percent', 0),
                'disk': record.get('disk_percent', 0),
                'agent_ip': record.get('agent_ip', '')
            })
        
        logging.info(f"Dati real-time recuperati: {len(formatted_data)} record per {timespan}")
        return jsonify(formatted_data)
        
    except Exception as e:
        logging.error(f"Errore nel recupero dei dati real-time: {e}", exc_info=True)
        return jsonify({'error': 'Errore interno del server'}), 500


@app.route('/api/agents', methods=['GET'])
@requires_auth
@validate_input
@rate_limit(requests_per_minute=30, requests_per_hour=500)
def get_agents():
    """
    Endpoint per ottenere la lista degli agent attivi.
    """
    try:
        agents_data = database.get_active_agents()
        
        # Formatta i dati degli agent
        agents = []
        for i, agent in enumerate(agents_data, 1):
            # Determina lo stato in base all'ultimo aggiornamento
            last_update = agent.get('timestamp', 0)
            current_time = time.time()
            time_diff = current_time - last_update
            
            if time_diff < 120:  # Meno di 2 minuti
                status = 'online'
            elif time_diff < 300:  # Meno di 5 minuti
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
        
        logging.info(f"Lista agent recuperata: {len(agents)} agent")
        return jsonify(agents)
        
    except Exception as e:
        logging.error(f"Errore nel recupero degli agent: {e}", exc_info=True)
        return jsonify({'error': 'Errore interno del server'}), 500


@app.route('/api/agents/<int:agent_id>', methods=['GET'])
@requires_auth
@validate_input
@rate_limit(requests_per_minute=30, requests_per_hour=500)
def get_agent(agent_id):
    """
    Endpoint per ottenere i dettagli di un agent specifico.
    """
    try:
        agent_data = database.get_agent_details(agent_id)
        
        if not agent_data:
            return jsonify({'error': 'Agent non trovato'}), 404
        
        logging.info(f"Dettagli agent {agent_id} recuperati")
        return jsonify(agent_data)
        
    except Exception as e:
        logging.error(f"Errore nel recupero dell'agent {agent_id}: {e}", exc_info=True)
        return jsonify({'error': 'Errore interno del server'}), 500


@app.route('/api/alerts', methods=['GET'])
@requires_auth
@validate_input
@rate_limit(requests_per_minute=30, requests_per_hour=500)
def get_alerts():
    """
    Endpoint per ottenere gli avvisi attivi del sistema.
    """
    try:
        alerts = database.get_active_alerts()
        
        # Se non ci sono avvisi nel database, genera avvisi basati sui dati correnti
        if not alerts:
            alerts = database.generate_alerts_from_current_data()
        
        logging.info(f"Avvisi recuperati: {len(alerts)} avvisi attivi")
        return jsonify(alerts)
        
    except Exception as e:
        logging.error(f"Errore nel recupero degli avvisi: {e}", exc_info=True)
        return jsonify({'error': 'Errore interno del server'}), 500


@app.route('/api/alerts/<alert_id>/dismiss', methods=['POST'])
@requires_auth
@validate_input
@rate_limit(requests_per_minute=20, requests_per_hour=200)
def dismiss_alert(alert_id):
    """
    Endpoint per dismissare un avviso.
    """
    try:
        success = database.dismiss_alert(alert_id)
        
        if success:
            logging.info(f"Avviso {alert_id} dismissato")
            return jsonify({'message': 'Avviso dismissato con successo'})
        else:
            return jsonify({'error': 'Avviso non trovato'}), 404
        
    except Exception as e:
        logging.error(f"Errore nel dismissal dell'avviso {alert_id}: {e}", exc_info=True)
        return jsonify({'error': 'Errore interno del server'}), 500


@app.route('/api/health', methods=['GET'])
@requires_auth
@validate_input
@rate_limit(requests_per_minute=60, requests_per_hour=1000)
def get_system_health():
    """
    Endpoint per ottenere lo stato di salute del sistema.
    """
    try:
        health_data = {
            'status': 'healthy',
            'timestamp': time.time(),
            'server_uptime': time.time() - start_time if 'start_time' in globals() else 0,
            'database_status': 'connected',
            'ssl_enabled': use_https if 'use_https' in globals() else False,
            'version': '1.0.0'
        }
        
        logging.info("Stato di salute del sistema recuperato")
        return jsonify(health_data)
        
    except Exception as e:
        logging.error(f"Errore nel recupero dello stato di salute: {e}", exc_info=True)
        return jsonify({'error': 'Errore interno del server'}), 500


# --- Endpoint per servire la dashboard web ---

@app.route('/', methods=['GET'])
def dashboard():
    """
    Serve la dashboard web principale.
    """
    try:
        return app.send_static_file('index.html')
    except Exception as e:
        logging.error(f"Errore nel servire la dashboard: {e}", exc_info=True)
        return "Errore nel caricamento della dashboard", 500

if __name__ == '__main__':
    if USERNAME is None or PASSWORD_HASH is None:
        logging.critical("Credenziali non configurate. Impossibile avviare il server.")
        sys.exit(1)
    try:
        logging.info("Avvio del server NetMaster...")
        logging.info(f"Username configurato: {USERNAME}")
        
        # Configurazione SSL/HTTPS
        ssl_mgr = ssl_manager.create_ssl_manager()
        use_https = True
        
        try:
            # Configura SSL (genera certificati se necessario)
            if ssl_mgr.setup_ssl():
                ssl_context = ssl_mgr.get_ssl_context(check_hostname=False)
                logging.info("[HTTPS] Server in ascolto su https://localhost:5000")
                logging.info("[HTTPS] Certificati SSL configurati correttamente")
            else:
                logging.warning("[HTTPS] Impossibile configurare SSL, fallback su HTTP")
                use_https = False
                ssl_context = None
        except Exception as e:
            logging.warning(f"[HTTPS] Errore SSL: {e}, fallback su HTTP")
            use_https = False
            ssl_context = None
        
        if not use_https:
            logging.info("[HTTP] Server in ascolto su http://localhost:5000")
            logging.warning("[SICUREZZA] Comunicazioni non criptate - considera l'uso di HTTPS")
        
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
