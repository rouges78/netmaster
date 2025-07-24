#!/usr/bin/env python3
"""
NetMaster Monitoring Suite - Configurazione Produzione
Configurazione ottimizzata per ambiente di produzione
"""

import os
import logging
from logging.handlers import RotatingFileHandler

class ProductionConfig:
    """Configurazione per ambiente di produzione."""
    
    # Server Configuration
    HOST = os.getenv('NETMASTER_HOST', '0.0.0.0')
    PORT = int(os.getenv('NETMASTER_PORT', 5000))
    DEBUG = False
    TESTING = False
    
    # Security Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(32))
    USE_HTTPS = os.getenv('USE_HTTPS', 'true').lower() == 'true'
    SSL_CERT_PATH = os.getenv('SSL_CERT_PATH', 'ssl/server.crt')
    SSL_KEY_PATH = os.getenv('SSL_KEY_PATH', 'ssl/server.key')
    
    # Database Configuration
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'netmaster_production.db')
    DATABASE_BACKUP_INTERVAL = int(os.getenv('DATABASE_BACKUP_INTERVAL', 3600))  # 1 ora
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/netmaster_production.log')
    LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', 10485760))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', 5))
    
    # Performance Configuration
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', 4))
    RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', 60))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 30))
    
    # Monitoring Configuration
    AGENT_TIMEOUT = int(os.getenv('AGENT_TIMEOUT', 300))  # 5 minuti
    DATA_RETENTION_DAYS = int(os.getenv('DATA_RETENTION_DAYS', 30))
    ALERT_COOLDOWN = int(os.getenv('ALERT_COOLDOWN', 300))  # 5 minuti
    
    # Email Configuration (per notifiche)
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    EMAIL_USERNAME = os.getenv('EMAIL_USERNAME', '')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
    
    @staticmethod
    def setup_production_logging():
        """Configura logging per produzione."""
        # Crea directory logs se non esiste
        os.makedirs('logs', exist_ok=True)
        
        # Configurazione logging con rotazione
        logging.basicConfig(
            level=getattr(logging, ProductionConfig.LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                RotatingFileHandler(
                    ProductionConfig.LOG_FILE,
                    maxBytes=ProductionConfig.LOG_MAX_BYTES,
                    backupCount=ProductionConfig.LOG_BACKUP_COUNT
                ),
                logging.StreamHandler()  # Console output
            ]
        )
        
        # Disabilita logging verbose di werkzeug in produzione
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
        
        return logging.getLogger(__name__)
    
    @staticmethod
    def validate_config():
        """Valida configurazione produzione."""
        errors = []
        
        # Verifica credenziali
        if not os.getenv('NETMASTER_USERNAME'):
            errors.append("NETMASTER_USERNAME non configurato")
        if not os.getenv('NETMASTER_PASSWORD_HASH'):
            errors.append("NETMASTER_PASSWORD_HASH non configurato")
        
        # Verifica SSL se abilitato
        if ProductionConfig.USE_HTTPS:
            if not os.path.exists(ProductionConfig.SSL_CERT_PATH):
                errors.append(f"Certificato SSL non trovato: {ProductionConfig.SSL_CERT_PATH}")
            if not os.path.exists(ProductionConfig.SSL_KEY_PATH):
                errors.append(f"Chiave SSL non trovata: {ProductionConfig.SSL_KEY_PATH}")
        
        # Verifica directory
        required_dirs = ['logs', 'ssl', 'backups']
        for dir_name in required_dirs:
            if not os.path.exists(dir_name):
                os.makedirs(dir_name, exist_ok=True)
        
        return errors

def get_production_config():
    """Restituisce configurazione produzione validata."""
    config = ProductionConfig()
    errors = config.validate_config()
    
    if errors:
        raise ValueError(f"Errori configurazione produzione: {', '.join(errors)}")
    
    return config
