import sqlite3
import os
import logging
from datetime import datetime
import json

DB_PATH = os.path.join('data', 'monitoring.db')

def get_db_connection():
    """Crea e restituisce una connessione al database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Crea il database e le tabelle necessarie se non esistono."""
    db_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
        logging.info(f"Creata directory per il database: {db_dir}")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Tabella per i dati di sistema
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    agent_ip TEXT NOT NULL,
                    agent_name TEXT,
                    cpu_usage REAL NOT NULL,
                    memory_usage REAL NOT NULL,
                    disk_usage REAL NOT NULL,
                    system TEXT NOT NULL,
                    node TEXT NOT NULL,
                    release TEXT NOT NULL,
                    version TEXT NOT NULL
                )
            ''')
            
            # Tabella per le soglie
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS thresholds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_ip TEXT NOT NULL,
                    metric TEXT NOT NULL,
                    threshold REAL NOT NULL,
                    enabled BOOLEAN NOT NULL DEFAULT 1,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    UNIQUE(agent_ip, metric)
                )
            ''')
            
            # Tabella per le notifiche
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_ip TEXT NOT NULL,
                    metric TEXT NOT NULL,
                    value REAL NOT NULL,
                    threshold REAL NOT NULL,
                    timestamp DATETIME NOT NULL,
                    status TEXT NOT NULL
                )
            ''')
            
            # Tabella per la configurazione delle notifiche
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notification_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL UNIQUE,
                    config JSON NOT NULL,
                    enabled BOOLEAN NOT NULL DEFAULT 1,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
            ''')
            
            conn.commit()
            logging.info("Database inizializzato con successo.")
    except Exception as e:
        logging.error(f"Errore durante l'inizializzazione del database: {e}", exc_info=True)

def save_system_data(data, agent_ip):
    """Salva i dati di sistema ricevuti da un agent nel database."""
    sql = '''
        INSERT INTO system_data (
            timestamp, agent_ip, agent_name, cpu_usage, memory_usage, disk_usage,
            system, node, release, version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    params = (
        datetime.now().isoformat(),
        agent_ip,
        data.get('node', 'N/A'),
        data['cpu_usage'],
        data['memory'],
        data['disk'],
        data['system'],
        data['node'],
        data['release'],
        data['version']
    )
    try:
        with get_db_connection() as conn:
            conn.execute(sql, params)
            conn.commit()
        return True
    except Exception as e:
        logging.error(f"Errore durante il salvataggio dei dati: {e}", exc_info=True)
        return False

def get_notification_config(config_type='email'):
    """Recupera la configurazione per un tipo di notifica."""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT config FROM notification_config WHERE type = ? AND enabled = 1", (config_type,))
            row = cursor.fetchone()
        if row:
            return json.loads(row['config'])
    except Exception as e:
        logging.error(f"Errore nel recupero della config di notifica: {e}", exc_info=True)
    return None

def get_thresholds_for_agent(agent_ip):
    """Recupera le soglie attive per un dato agent."""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT metric, threshold FROM thresholds WHERE agent_ip = ? AND enabled = 1", (agent_ip,))
            return cursor.fetchall()
    except Exception as e:
        logging.error(f"Errore nel recupero delle soglie per l'agent {agent_ip}: {e}", exc_info=True)
        return []

def has_recent_notification(agent_ip, metric):
    """Verifica se è già stata inviata una notifica recente per una metrica."""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT id FROM notifications WHERE agent_ip = ? AND metric = ? AND timestamp > datetime('now', '-1 hour')", (agent_ip, metric))
            return cursor.fetchone() is not None
    except Exception as e:
        logging.error(f"Errore nel controllo delle notifiche recenti: {e}", exc_info=True)
        return False

def save_notification(agent_ip, metric, value, threshold):
    """Salva una notifica nel database."""
    sql = "INSERT INTO notifications (agent_ip, metric, value, threshold, timestamp, status) VALUES (?, ?, ?, ?, ?, ?)"
    params = (agent_ip, metric, value, threshold, datetime.now().isoformat(), 'sent')
    try:
        with get_db_connection() as conn:
            conn.execute(sql, params)
            conn.commit()
    except Exception as e:
        logging.error(f"Errore nel salvataggio della notifica: {e}", exc_info=True)

def get_all_thresholds():
    """Recupera tutte le soglie configurate."""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT agent_ip, metric, threshold, enabled FROM thresholds ORDER BY agent_ip, metric")
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logging.error(f"Errore nel recupero di tutte le soglie: {e}", exc_info=True)
        return []

def save_threshold(agent_ip, metric, threshold, enabled):
    """Salva o aggiorna una soglia."""
    sql = "INSERT OR REPLACE INTO thresholds (agent_ip, metric, threshold, enabled, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)"
    now = datetime.now().isoformat()
    params = (agent_ip, metric, threshold, enabled, now, now)
    try:
        with get_db_connection() as conn:
            conn.execute(sql, params)
            conn.commit()
        return True
    except Exception as e:
        logging.error(f"Errore nel salvataggio della soglia: {e}", exc_info=True)
        return False

def get_all_notification_configs():
    """Recupera tutte le configurazioni di notifica."""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT type, config, enabled FROM notification_config")
            results = []
            for row in cursor.fetchall():
                r = dict(row)
                r['config'] = json.loads(r['config'])
                results.append(r)
            return results
    except Exception as e:
        logging.error(f"Errore nel recupero delle config di notifica: {e}", exc_info=True)
        return []

def save_notification_config(config_type, config, enabled):
    """Salva o aggiorna una configurazione di notifica."""
    sql = "INSERT OR REPLACE INTO notification_config (type, config, enabled, created_at, updated_at) VALUES (?, ?, ?, ?, ?)"
    now = datetime.now().isoformat()
    params = (config_type, json.dumps(config), enabled, now, now)
    try:
        with get_db_connection() as conn:
            conn.execute(sql, params)
            conn.commit()
        return True
    except Exception as e:
        logging.error(f"Errore nel salvataggio della config di notifica: {e}", exc_info=True)
        return False

def get_history(agent_ip=None, start_date=None, end_date=None, limit=100):
    """Recupera i dati storici con filtri opzionali."""
    query = "SELECT * FROM system_data"
    params = []
    conditions = []
    
    if agent_ip:
        conditions.append("agent_ip = ?")
        params.append(agent_ip)
    if start_date:
        conditions.append("timestamp >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("timestamp <= ?")
        params.append(end_date)
        
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
        
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    
    try:
        with get_db_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logging.error(f"Errore nel recupero della cronologia: {e}", exc_info=True)
        return []


# --- Nuove funzioni per supportare la dashboard web ---

def get_system_stats():
    """
    Recupera le statistiche aggregate del sistema per la dashboard.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Recupera i dati più recenti per ogni agent (ultimi 5 minuti)
            query = """
                SELECT agent_ip, agent_name, cpu_usage, memory_usage, disk_usage, 
                       system, release, timestamp
                FROM system_data 
                WHERE timestamp > datetime('now', '-5 minutes')
                ORDER BY timestamp DESC
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # Converte in formato dict per compatibilità
            stats = []
            for row in rows:
                stats.append({
                    'agent_ip': row['agent_ip'],
                    'agent_name': row.get('agent_name', row['agent_ip']),
                    'cpu_percent': row['cpu_usage'],
                    'memory_percent': row['memory_usage'],
                    'disk_percent': row['disk_usage'],
                    'platform': f"{row['system']} {row['release']}",
                    'timestamp': row['timestamp']
                })
            
            return stats
            
    except Exception as e:
        logging.error(f"Errore nel recupero delle statistiche: {e}", exc_info=True)
        return []


def get_recent_data(hours=6):
    """
    Recupera i dati recenti per i grafici real-time.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT timestamp, agent_ip, agent_name, cpu_usage, memory_usage, disk_usage
                FROM system_data 
                WHERE timestamp > datetime('now', '-{} hours')
                ORDER BY timestamp ASC
            """.format(hours)
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # Converte timestamp in formato Unix per JavaScript
            import time
            from datetime import datetime
            
            formatted_data = []
            for row in rows:
                # Converte timestamp SQLite in Unix timestamp
                try:
                    dt = datetime.fromisoformat(row['timestamp'].replace('Z', '+00:00'))
                    unix_timestamp = dt.timestamp()
                except:
                    # Fallback per formati timestamp diversi
                    unix_timestamp = time.time()
                
                formatted_data.append({
                    'timestamp': unix_timestamp,
                    'agent_ip': row['agent_ip'],
                    'cpu_percent': row['cpu_usage'],
                    'memory_percent': row['memory_usage'],
                    'disk_percent': row['disk_usage']
                })
            
            return formatted_data
            
    except Exception as e:
        logging.error(f"Errore nel recupero dei dati recenti: {e}", exc_info=True)
        return []


def get_active_agents():
    """
    Recupera la lista degli agent attivi con i loro ultimi dati.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Recupera l'ultimo record per ogni agent
            query = """
                SELECT s1.* FROM system_data s1
                INNER JOIN (
                    SELECT agent_ip, MAX(timestamp) as max_timestamp
                    FROM system_data
                    GROUP BY agent_ip
                ) s2 ON s1.agent_ip = s2.agent_ip AND s1.timestamp = s2.max_timestamp
                ORDER BY s1.timestamp DESC
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # Converte in formato dict con timestamp Unix
            import time
            from datetime import datetime
            
            agents = []
            for row in rows:
                # Converte timestamp
                try:
                    dt = datetime.fromisoformat(row['timestamp'].replace('Z', '+00:00'))
                    unix_timestamp = dt.timestamp()
                except:
                    unix_timestamp = time.time()
                
                agents.append({
                    'agent_ip': row['agent_ip'],
                    'hostname': row.get('agent_name', row['agent_ip']),
                    'cpu_percent': row['cpu_usage'],
                    'memory_percent': row['memory_usage'],
                    'disk_percent': row['disk_usage'],
                    'platform': f"{row['system']} {row['release']}",
                    'architecture': row.get('version', 'Unknown'),
                    'timestamp': unix_timestamp,
                    'processes': 0,  # Placeholder - da implementare se necessario
                    'uptime': 0      # Placeholder - da implementare se necessario
                })
            
            return agents
            
    except Exception as e:
        logging.error(f"Errore nel recupero degli agent attivi: {e}", exc_info=True)
        return []


def get_agent_details(agent_id):
    """
    Recupera i dettagli di un agent specifico.
    Nota: agent_id è un indice numerico, non l'IP dell'agent.
    """
    try:
        agents = get_active_agents()
        
        if 1 <= agent_id <= len(agents):
            return agents[agent_id - 1]  # agent_id è 1-based
        else:
            return None
            
    except Exception as e:
        logging.error(f"Errore nel recupero dei dettagli dell'agent {agent_id}: {e}", exc_info=True)
        return None


def get_active_alerts():
    """
    Recupera gli avvisi attivi dal database.
    Per ora restituisce una lista vuota - gli avvisi saranno generati dinamicamente.
    """
    try:
        # Implementazione futura: tabella alerts nel database
        # Per ora restituisce lista vuota e usa generate_alerts_from_current_data
        return []
        
    except Exception as e:
        logging.error(f"Errore nel recupero degli avvisi: {e}", exc_info=True)
        return []


def generate_alerts_from_current_data():
    """
    Genera avvisi basati sui dati correnti e le soglie configurate.
    """
    try:
        import time
        
        alerts = []
        current_time = time.time()
        
        # Recupera dati recenti e soglie
        recent_data = get_system_stats()
        thresholds = get_all_thresholds()
        
        # Crea un dizionario delle soglie per agent
        threshold_map = {}
        for threshold in thresholds:
            agent_ip = threshold['agent_ip']
            metric = threshold['metric']
            if agent_ip not in threshold_map:
                threshold_map[agent_ip] = {}
            threshold_map[agent_ip][metric] = threshold['threshold']
        
        # Genera avvisi per ogni agent
        alert_id = 1
        for data in recent_data:
            agent_ip = data['agent_ip']
            hostname = data.get('agent_name', agent_ip)
            
            # Soglie di default se non configurate
            cpu_threshold = threshold_map.get(agent_ip, {}).get('cpu', 75)
            memory_threshold = threshold_map.get(agent_ip, {}).get('memory', 85)
            disk_threshold = threshold_map.get(agent_ip, {}).get('disk', 90)
            
            # Controlla CPU
            if data['cpu_percent'] > cpu_threshold:
                alerts.append({
                    'id': str(alert_id),
                    'type': 'cpu',
                    'severity': 'critical' if data['cpu_percent'] > 90 else 'warning',
                    'title': 'CPU Elevata',
                    'message': f"{hostname}: CPU al {data['cpu_percent']:.1f}% (soglia: {cpu_threshold}%)",
                    'timestamp': current_time - 300,  # 5 minuti fa
                    'active': True,
                    'agent_hostname': hostname
                })
                alert_id += 1
            
            # Controlla Memoria
            if data['memory_percent'] > memory_threshold:
                alerts.append({
                    'id': str(alert_id),
                    'type': 'memory',
                    'severity': 'critical' if data['memory_percent'] > 95 else 'warning',
                    'title': 'Memoria Elevata',
                    'message': f"{hostname}: Memoria al {data['memory_percent']:.1f}% (soglia: {memory_threshold}%)",
                    'timestamp': current_time - 180,  # 3 minuti fa
                    'active': True,
                    'agent_hostname': hostname
                })
                alert_id += 1
            
            # Controlla Disco
            if data['disk_percent'] > disk_threshold:
                alerts.append({
                    'id': str(alert_id),
                    'type': 'disk',
                    'severity': 'warning',
                    'title': 'Spazio Disco Basso',
                    'message': f"{hostname}: Disco al {data['disk_percent']:.1f}% (soglia: {disk_threshold}%)",
                    'timestamp': current_time - 600,  # 10 minuti fa
                    'active': True,
                    'agent_hostname': hostname
                })
                alert_id += 1
        
        # Controlla agent offline (ultimi dati più vecchi di 5 minuti)
        all_agents = get_active_agents()
        for agent in all_agents:
            time_diff = current_time - agent['timestamp']
            if time_diff > 300:  # 5 minuti
                alerts.append({
                    'id': str(alert_id),
                    'type': 'system',
                    'severity': 'error',
                    'title': 'Agent Offline',
                    'message': f"{agent['hostname']} non risponde da {int(time_diff/60)} minuti",
                    'timestamp': current_time - time_diff,
                    'active': True,
                    'agent_hostname': agent['hostname']
                })
                alert_id += 1
        
        return alerts
        
    except Exception as e:
        logging.error(f"Errore nella generazione degli avvisi: {e}", exc_info=True)
        return []


def dismiss_alert(alert_id):
    """
    Dismisses un avviso specifico.
    Per ora simula il dismiss - implementazione futura con tabella alerts.
    """
    try:
        # Implementazione futura: aggiorna tabella alerts
        # Per ora simula sempre successo
        logging.info(f"Avviso {alert_id} dismissato (simulato)")
        return True
        
    except Exception as e:
        logging.error(f"Errore nel dismiss dell'avviso {alert_id}: {e}", exc_info=True)
        return False
