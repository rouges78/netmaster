#!/usr/bin/env python3
"""
Server di test per la dashboard NetMaster
Versione semplificata per testare la dashboard web senza conflitti
"""

import logging
import json
import os
import sys
import time
from datetime import datetime

from flask import Flask, request, jsonify, send_from_directory
from functools import wraps

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crea app Flask
app = Flask(__name__, static_folder='static')

# Credenziali di test
TEST_USERNAME = 'admin'
TEST_PASSWORD = 'password'

def requires_auth(f):
    """Decoratore per autenticazione Basic semplificata"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != TEST_USERNAME or auth.password != TEST_PASSWORD:
            return jsonify({'error': 'Autenticazione richiesta'}), 401
        return f(*args, **kwargs)
    return decorated_function

# --- ENDPOINT DASHBOARD ---

@app.route('/')
def dashboard():
    """Serve la dashboard web principale"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/test.html')
def test_page():
    """Serve la pagina di test"""
    return send_from_directory(app.static_folder, 'test.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve i file statici"""
    return send_from_directory(app.static_folder, filename)

@app.route('/css/<path:filename>')
def css_files(filename):
    """Serve i file CSS"""
    return send_from_directory(os.path.join(app.static_folder, 'css'), filename)

@app.route('/js/<path:filename>')
def js_files(filename):
    """Serve i file JavaScript"""
    return send_from_directory(os.path.join(app.static_folder, 'js'), filename)

@app.route('/api/stats')
@requires_auth
def get_stats():
    """Endpoint per statistiche aggregate"""
    return jsonify({
        'total_agents': 3,
        'avg_cpu': 45.2,
        'avg_memory': 67.8,
        'avg_disk': 23.4,
        'active_alerts': 2
    })

@app.route('/api/realtime')
@requires_auth
def get_realtime_data():
    """Endpoint per dati real-time"""
    timespan = request.args.get('timespan', '6h')
    
    # Genera dati mock per test
    now = time.time() * 1000
    data = []
    
    # Genera 72 punti dati (6 ore, ogni 5 minuti)
    for i in range(72):
        timestamp = now - (i * 5 * 60 * 1000)
        data.append({
            'timestamp': timestamp,
            'cpu': 30 + (i % 40),
            'memory': 50 + (i % 30),
            'disk': 20 + (i % 20)
        })
    
    return jsonify(data[::-1])  # Inverti per ordine cronologico

@app.route('/api/agents')
@requires_auth
def get_agents():
    """Endpoint per lista agent"""
    current_time = time.time()
    
    agents = [
        {
            'id': 1,
            'hostname': 'PC-UFFICIO-01',
            'ip_address': '192.168.1.100',
            'cpu_percent': 45.2,
            'memory_percent': 67.8,
            'disk_percent': 23.4,
            'processes': 156,
            'uptime': 86400,
            'platform': 'Windows 11',
            'architecture': 'x64',
            'last_update': current_time - 30,
            'status': 'online'
        },
        {
            'id': 2,
            'hostname': 'PC-UFFICIO-02',
            'ip_address': '192.168.1.101',
            'cpu_percent': 78.5,
            'memory_percent': 89.2,
            'disk_percent': 45.7,
            'processes': 203,
            'uptime': 172800,
            'platform': 'Windows 10',
            'architecture': 'x64',
            'last_update': current_time - 45,
            'status': 'warning'
        },
        {
            'id': 3,
            'hostname': 'SERVER-01',
            'ip_address': '192.168.1.10',
            'cpu_percent': 23.1,
            'memory_percent': 45.6,
            'disk_percent': 67.8,
            'processes': 89,
            'uptime': 2592000,
            'platform': 'Ubuntu 22.04',
            'architecture': 'x64',
            'last_update': current_time - 15,
            'status': 'online'
        }
    ]
    
    return jsonify(agents)

@app.route('/api/alerts')
@requires_auth
def get_alerts():
    """Endpoint per avvisi"""
    current_time = time.time()
    
    alerts = [
        {
            'id': '1',
            'type': 'cpu',
            'severity': 'warning',
            'title': 'CPU Elevata',
            'message': 'PC-UFFICIO-02: CPU al 78.5% (soglia: 75%)',
            'timestamp': current_time - 300,
            'active': True,
            'agent_hostname': 'PC-UFFICIO-02'
        },
        {
            'id': '2',
            'type': 'memory',
            'severity': 'critical',
            'title': 'Memoria Critica',
            'message': 'PC-UFFICIO-02: Memoria al 89.2% (soglia: 85%)',
            'timestamp': current_time - 180,
            'active': True,
            'agent_hostname': 'PC-UFFICIO-02'
        }
    ]
    
    return jsonify(alerts)

@app.route('/api/alerts/<alert_id>/dismiss', methods=['POST'])
@requires_auth
def dismiss_alert(alert_id):
    """Endpoint per dismissare avvisi"""
    logger.info(f"Avviso {alert_id} dismissato")
    return jsonify({'message': 'Avviso dismissato con successo'})

@app.route('/api/health')
@requires_auth
def get_system_health():
    """Endpoint per stato di salute"""
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time(),
        'server_uptime': 3600,
        'database_status': 'connected',
        'ssl_enabled': False,
        'version': '1.0.0-test'
    })

@app.route('/api/history')
@requires_auth
def get_history():
    """Endpoint per storico dati"""
    # Genera dati storici mock
    now = time.time()
    history = []
    
    for i in range(100):
        timestamp = now - (i * 3600)  # Ogni ora
        history.append({
            'timestamp': timestamp,
            'agent_ip': '192.168.1.100',
            'hostname': 'PC-UFFICIO-01',
            'cpu_percent': 30 + (i % 50),
            'memory_percent': 40 + (i % 40),
            'disk_percent': 20 + (i % 30),
            'platform': 'Windows 11'
        })
    
    return jsonify(history)

@app.route('/api/thresholds')
@requires_auth
def get_thresholds():
    """Endpoint per soglie"""
    return jsonify({
        'cpu': 75,
        'memory': 85,
        'disk': 90
    })

@app.route('/api/notifications/config')
@requires_auth
def get_email_config():
    """Endpoint per configurazione email"""
    return jsonify({
        'enabled': True,
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'username': 'test@example.com'
    })

if __name__ == '__main__':
    logger.info("Avvio server di test NetMaster Dashboard...")
    logger.info(f"Dashboard disponibile su: http://localhost:5000")
    logger.info(f"Credenziali: {TEST_USERNAME} / {TEST_PASSWORD}")
    
    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            threaded=True
        )
    except KeyboardInterrupt:
        logger.info("Server interrotto dall'utente.")
    except Exception as e:
        logger.error(f"Errore durante l'avvio del server: {e}")
        sys.exit(1)
