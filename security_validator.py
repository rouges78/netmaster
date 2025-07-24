"""
Modulo per la validazione e sicurezza degli input del server NetMaster.
Implementa sanitizzazione, rate limiting e validazione rigorosa dei dati.
"""

import re
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from functools import wraps
from flask import request, jsonify, g

logger = logging.getLogger(__name__)

class SecurityError(Exception):
    """Eccezione per errori di sicurezza."""
    pass

class ValidationError(Exception):
    """Eccezione per errori di validazione."""
    pass

class RateLimiter:
    """Implementa rate limiting per IP."""
    
    def __init__(self):
        self.requests = {}  # {ip: [(timestamp, endpoint), ...]}
        self.cleanup_interval = 300  # 5 minuti
        self.last_cleanup = time.time()
    
    def cleanup_old_requests(self):
        """Rimuove le richieste vecchie per liberare memoria."""
        current_time = time.time()
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        cutoff_time = current_time - 3600  # Mantieni solo l'ultima ora
        for ip in list(self.requests.keys()):
            self.requests[ip] = [
                (timestamp, endpoint) for timestamp, endpoint in self.requests[ip]
                if timestamp > cutoff_time
            ]
            if not self.requests[ip]:
                del self.requests[ip]
        
        self.last_cleanup = current_time
    
    def is_rate_limited(self, ip: str, endpoint: str, 
                       requests_per_minute: int = 60, 
                       requests_per_hour: int = 1000) -> tuple[bool, str]:
        """
        Verifica se un IP ha superato i limiti di rate.
        
        Args:
            ip: Indirizzo IP
            endpoint: Endpoint richiesto
            requests_per_minute: Limite richieste per minuto
            requests_per_hour: Limite richieste per ora
            
        Returns:
            tuple: (is_limited, reason)
        """
        self.cleanup_old_requests()
        
        current_time = time.time()
        
        if ip not in self.requests:
            self.requests[ip] = []
        
        # Conta richieste nell'ultimo minuto
        minute_ago = current_time - 60
        minute_requests = sum(1 for timestamp, _ in self.requests[ip] 
                             if timestamp > minute_ago)
        
        if minute_requests >= requests_per_minute:
            return True, f"Troppo richieste per minuto ({minute_requests}/{requests_per_minute})"
        
        # Conta richieste nell'ultima ora
        hour_ago = current_time - 3600
        hour_requests = sum(1 for timestamp, _ in self.requests[ip] 
                           if timestamp > hour_ago)
        
        if hour_requests >= requests_per_hour:
            return True, f"Troppo richieste per ora ({hour_requests}/{requests_per_hour})"
        
        # Registra la richiesta
        self.requests[ip].append((current_time, endpoint))
        return False, ""

# Istanza globale del rate limiter
rate_limiter = RateLimiter()

class InputValidator:
    """Validatore per input del server."""
    
    # Pattern per validazione
    PATTERNS = {
        'hostname': re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$'),
        'ip_address': re.compile(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'),
        'safe_string': re.compile(r'^[a-zA-Z0-9\s\-_\.@]+$'),
        'numeric': re.compile(r'^\d+(\.\d+)?$')
    }
    
    # Limiti per i valori
    LIMITS = {
        'string_max_length': 1000,
        'cpu_max': 100.0,
        'memory_max': 100.0,
        'disk_max': 100.0,
        'processes_max': 10000,
        'uptime_max': 365 * 24 * 3600  # 1 anno in secondi
    }
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = None) -> str:
        """
        Sanitizza una stringa rimuovendo caratteri pericolosi.
        
        Args:
            value: Stringa da sanitizzare
            max_length: Lunghezza massima
            
        Returns:
            str: Stringa sanitizzata
        """
        if not isinstance(value, str):
            raise ValidationError(f"Valore deve essere una stringa, ricevuto: {type(value)}")
        
        # Rimuovi caratteri di controllo
        sanitized = ''.join(char for char in value if ord(char) >= 32 or char in '\t\n\r')
        
        # Limita lunghezza
        max_len = max_length or InputValidator.LIMITS['string_max_length']
        if len(sanitized) > max_len:
            logger.warning(f"Stringa troncata da {len(sanitized)} a {max_len} caratteri")
            sanitized = sanitized[:max_len]
        
        return sanitized.strip()
    
    @staticmethod
    def validate_system_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida e sanitizza i dati di sistema ricevuti dall'agent.
        
        Args:
            data: Dati da validare
            
        Returns:
            Dict: Dati validati e sanitizzati
            
        Raises:
            ValidationError: Se i dati non sono validi
        """
        if not isinstance(data, dict):
            raise ValidationError("I dati devono essere un oggetto JSON")
        
        # Campi obbligatori
        required_fields = ['hostname', 'ip_address', 'timestamp', 'cpu_percent', 
                          'memory_percent', 'disk_percent']
        
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Campo obbligatorio mancante: {field}")
        
        validated_data = {}
        
        # Valida hostname
        hostname = InputValidator.sanitize_string(data['hostname'], 255)
        if not InputValidator.PATTERNS['hostname'].match(hostname):
            raise ValidationError(f"Hostname non valido: {hostname}")
        validated_data['hostname'] = hostname
        
        # Valida IP address
        ip_address = InputValidator.sanitize_string(data['ip_address'], 15)
        if not InputValidator.PATTERNS['ip_address'].match(ip_address):
            raise ValidationError(f"Indirizzo IP non valido: {ip_address}")
        validated_data['ip_address'] = ip_address
        
        # Valida timestamp
        try:
            timestamp = float(data['timestamp'])
            current_time = time.time()
            # Accetta timestamp nell'ultima ora o nel prossimo minuto (per clock skew)
            if not (current_time - 3600 <= timestamp <= current_time + 60):
                raise ValidationError(f"Timestamp fuori range: {timestamp}")
            validated_data['timestamp'] = timestamp
        except (ValueError, TypeError):
            raise ValidationError(f"Timestamp non valido: {data['timestamp']}")
        
        # Valida percentuali CPU, memoria, disco
        for field in ['cpu_percent', 'memory_percent', 'disk_percent']:
            try:
                value = float(data[field])
                if not (0 <= value <= 100):
                    raise ValidationError(f"{field} deve essere tra 0 e 100: {value}")
                validated_data[field] = round(value, 2)
            except (ValueError, TypeError):
                raise ValidationError(f"{field} non valido: {data[field]}")
        
        # Valida campi opzionali
        optional_fields = {
            'processes': ('int', 0, InputValidator.LIMITS['processes_max']),
            'uptime': ('float', 0, InputValidator.LIMITS['uptime_max']),
            'platform': ('str', None, 100),
            'architecture': ('str', None, 50)
        }
        
        for field, (field_type, min_val, max_val) in optional_fields.items():
            if field in data:
                try:
                    if field_type == 'int':
                        value = int(data[field])
                        if min_val is not None and value < min_val:
                            raise ValidationError(f"{field} troppo piccolo: {value}")
                        if max_val is not None and value > max_val:
                            raise ValidationError(f"{field} troppo grande: {value}")
                        validated_data[field] = value
                    elif field_type == 'float':
                        value = float(data[field])
                        if min_val is not None and value < min_val:
                            raise ValidationError(f"{field} troppo piccolo: {value}")
                        if max_val is not None and value > max_val:
                            raise ValidationError(f"{field} troppo grande: {value}")
                        validated_data[field] = round(value, 2)
                    elif field_type == 'str':
                        value = InputValidator.sanitize_string(data[field], max_val)
                        validated_data[field] = value
                except (ValueError, TypeError):
                    logger.warning(f"Campo opzionale {field} ignorato per valore non valido: {data[field]}")
        
        return validated_data
    
    @staticmethod
    def validate_json_request() -> Dict[str, Any]:
        """
        Valida che la richiesta contenga JSON valido.
        
        Returns:
            Dict: Dati JSON validati
            
        Raises:
            ValidationError: Se il JSON non è valido
        """
        if not request.is_json:
            raise ValidationError("Content-Type deve essere application/json")
        
        try:
            data = request.get_json(force=True)
            if data is None:
                raise ValidationError("Corpo della richiesta vuoto")
            return data
        except json.JSONDecodeError as e:
            raise ValidationError(f"JSON non valido: {e}")
        except Exception as e:
            raise ValidationError(f"Errore nel parsing JSON: {e}")

def rate_limit(requests_per_minute: int = 60, requests_per_hour: int = 1000):
    """
    Decoratore per implementare rate limiting.
    
    Args:
        requests_per_minute: Limite richieste per minuto
        requests_per_hour: Limite richieste per ora
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Ottieni IP del client
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            if client_ip:
                client_ip = client_ip.split(',')[0].strip()
            else:
                client_ip = 'unknown'
            
            # Verifica rate limit
            is_limited, reason = rate_limiter.is_rate_limited(
                client_ip, request.endpoint, requests_per_minute, requests_per_hour
            )
            
            if is_limited:
                logger.warning(f"[RATE_LIMIT] IP {client_ip} bloccato: {reason}")
                return jsonify({
                    'error': 'Rate limit superato',
                    'message': reason,
                    'retry_after': 60
                }), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_input(validation_func=None):
    """
    Decoratore per validare input delle richieste.
    
    Args:
        validation_func: Funzione personalizzata di validazione
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Validazione JSON di base
                data = InputValidator.validate_json_request()
                
                # Validazione personalizzata se fornita
                if validation_func:
                    data = validation_func(data)
                
                # Salva i dati validati in g per l'uso nella vista
                g.validated_data = data
                
                return f(*args, **kwargs)
                
            except ValidationError as e:
                logger.warning(f"[VALIDATION] Errore validazione da {request.remote_addr}: {e}")
                return jsonify({
                    'error': 'Dati non validi',
                    'message': str(e)
                }), 400
            except SecurityError as e:
                logger.error(f"[SECURITY] Tentativo di attacco da {request.remote_addr}: {e}")
                return jsonify({
                    'error': 'Richiesta non autorizzata',
                    'message': 'Richiesta bloccata per motivi di sicurezza'
                }), 403
            except Exception as e:
                logger.error(f"[ERROR] Errore imprevisto nella validazione: {e}", exc_info=True)
                return jsonify({
                    'error': 'Errore interno del server'
                }), 500
                
        return decorated_function
    return decorator

# Funzioni di utilità per logging sicurezza
def log_security_event(event_type: str, details: str, severity: str = "WARNING"):
    """
    Registra eventi di sicurezza.
    
    Args:
        event_type: Tipo di evento (es. "RATE_LIMIT", "VALIDATION_ERROR")
        details: Dettagli dell'evento
        severity: Severità (INFO, WARNING, ERROR, CRITICAL)
    """
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    log_message = f"[{event_type}] IP: {client_ip} | UA: {user_agent} | {details}"
    
    if severity == "INFO":
        logger.info(log_message)
    elif severity == "WARNING":
        logger.warning(log_message)
    elif severity == "ERROR":
        logger.error(log_message)
    elif severity == "CRITICAL":
        logger.critical(log_message)

if __name__ == "__main__":
    # Test del modulo di validazione
    logging.basicConfig(level=logging.INFO)
    
    print("[NETMASTER] Test del sistema di validazione")
    print("-" * 50)
    
    # Test validazione dati di sistema
    test_data = {
        'hostname': 'test-pc',
        'ip_address': '192.168.1.100',
        'timestamp': time.time(),
        'cpu_percent': 45.5,
        'memory_percent': 67.2,
        'disk_percent': 23.8,
        'processes': 156,
        'uptime': 86400,
        'platform': 'Windows',
        'architecture': 'x64'
    }
    
    try:
        validated = InputValidator.validate_system_data(test_data)
        print("[OK] Validazione dati di sistema completata")
        print(f"[INFO] Dati validati: {len(validated)} campi")
    except ValidationError as e:
        print(f"[ERRORE] Validazione fallita: {e}")
    
    # Test rate limiter
    rate_limiter_test = RateLimiter()
    test_ip = "192.168.1.1"
    
    print(f"[TEST] Rate limiter per IP {test_ip}")
    for i in range(5):
        is_limited, reason = rate_limiter_test.is_rate_limited(test_ip, "/api/test")
        if is_limited:
            print(f"[RATE_LIMIT] {reason}")
        else:
            print(f"[OK] Richiesta {i+1} accettata")
    
    print("[OK] Test completati")
