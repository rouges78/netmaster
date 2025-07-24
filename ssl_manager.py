"""
Modulo per la gestione SSL/TLS del server NetMaster.
Genera certificati auto-firmati per sviluppo e gestisce certificati di produzione.
"""

import os
import logging
import ssl
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

logger = logging.getLogger(__name__)

class SSLError(Exception):
    """Eccezione per errori SSL/TLS."""
    pass

class SSLManager:
    """Gestisce certificati SSL/TLS per il server NetMaster."""
    
    def __init__(self, cert_dir="certificates"):
        """
        Inizializza il gestore SSL.
        
        Args:
            cert_dir: Directory per salvare i certificati
        """
        self.cert_dir = cert_dir
        self.cert_file = os.path.join(cert_dir, "server.crt")
        self.key_file = os.path.join(cert_dir, "server.key")
        self.ca_file = os.path.join(cert_dir, "ca.crt")
        
        # Crea la directory se non esiste
        os.makedirs(cert_dir, exist_ok=True)
    
    def generate_self_signed_cert(self, hostname="localhost", days_valid=365):
        """
        Genera un certificato auto-firmato per sviluppo.
        
        Args:
            hostname: Nome host per il certificato
            days_valid: Giorni di validità del certificato
        """
        try:
            logger.info(f"[SSL] Generazione certificato auto-firmato per {hostname}")
            
            # Genera chiave privata
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            
            # Crea il soggetto del certificato
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "IT"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Italia"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "NetMaster"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "NetMaster Monitoring Suite"),
                x509.NameAttribute(NameOID.COMMON_NAME, hostname),
            ])
            
            # Crea il certificato
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=days_valid)
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName(hostname),
                    x509.DNSName("localhost"),
                    x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                ]),
                critical=False,
            ).add_extension(
                x509.BasicConstraints(ca=False, path_length=None),
                critical=True,
            ).add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    key_encipherment=True,
                    key_agreement=False,
                    key_cert_sign=False,
                    crl_sign=False,
                    content_commitment=False,
                    data_encipherment=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            ).sign(private_key, hashes.SHA256())
            
            # Salva la chiave privata
            with open(self.key_file, "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            # Salva il certificato
            with open(self.cert_file, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            # Copia il certificato come CA per l'agent
            with open(self.ca_file, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            logger.info(f"[SSL] Certificato generato con successo")
            logger.info(f"[SSL] Certificato: {self.cert_file}")
            logger.info(f"[SSL] Chiave privata: {self.key_file}")
            logger.info(f"[SSL] CA per agent: {self.ca_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"[SSL] Errore nella generazione del certificato: {e}")
            raise SSLError(f"Errore nella generazione del certificato: {e}")
    
    def certificate_exists(self):
        """
        Verifica se i certificati esistono.
        
        Returns:
            bool: True se certificato e chiave esistono
        """
        return os.path.exists(self.cert_file) and os.path.exists(self.key_file)
    
    def certificate_valid(self):
        """
        Verifica se il certificato è valido e non scaduto.
        
        Returns:
            bool: True se il certificato è valido
        """
        if not self.certificate_exists():
            return False
        
        try:
            with open(self.cert_file, "rb") as f:
                cert_data = f.read()
            
            cert = x509.load_pem_x509_certificate(cert_data)
            now = datetime.utcnow()
            
            # Verifica se il certificato è ancora valido
            if now < cert.not_valid_before or now > cert.not_valid_after:
                logger.warning("[SSL] Certificato scaduto o non ancora valido")
                return False
            
            logger.info("[SSL] Certificato valido")
            return True
            
        except Exception as e:
            logger.error(f"[SSL] Errore nella verifica del certificato: {e}")
            return False
    
    def get_ssl_context(self, check_hostname=True):
        """
        Crea un contesto SSL per il server Flask.
        
        Args:
            check_hostname: Se verificare il nome host
            
        Returns:
            ssl.SSLContext: Contesto SSL configurato
        """
        if not self.certificate_exists():
            raise SSLError("Certificati SSL non trovati. Esegui generate_self_signed_cert() prima.")
        
        try:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(self.cert_file, self.key_file)
            
            # Configurazioni di sicurezza
            context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
            context.options |= ssl.OP_NO_SSLv2
            context.options |= ssl.OP_NO_SSLv3
            context.options |= ssl.OP_NO_TLSv1
            context.options |= ssl.OP_NO_TLSv1_1
            
            if not check_hostname:
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
            
            logger.info("[SSL] Contesto SSL creato con successo")
            return context
            
        except Exception as e:
            logger.error(f"[SSL] Errore nella creazione del contesto SSL: {e}")
            raise SSLError(f"Errore nella creazione del contesto SSL: {e}")
    
    def get_client_ssl_context(self, verify_cert=False):
        """
        Crea un contesto SSL per il client (agent).
        
        Args:
            verify_cert: Se verificare il certificato del server
            
        Returns:
            ssl.SSLContext: Contesto SSL per il client
        """
        try:
            context = ssl.create_default_context()
            
            if not verify_cert:
                # Per certificati auto-firmati in sviluppo
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                logger.info("[SSL] Contesto client SSL creato (senza verifica certificato)")
            else:
                # Per certificati validi in produzione
                if os.path.exists(self.ca_file):
                    context.load_verify_locations(self.ca_file)
                logger.info("[SSL] Contesto client SSL creato (con verifica certificato)")
            
            return context
            
        except Exception as e:
            logger.error(f"[SSL] Errore nella creazione del contesto client SSL: {e}")
            raise SSLError(f"Errore nella creazione del contesto client SSL: {e}")
    
    def setup_ssl(self, hostname="localhost", force_regenerate=False):
        """
        Configura SSL generando certificati se necessario.
        
        Args:
            hostname: Nome host per il certificato
            force_regenerate: Forza la rigenerazione del certificato
            
        Returns:
            bool: True se SSL è configurato correttamente
        """
        try:
            # Verifica se i certificati esistono e sono validi
            if not force_regenerate and self.certificate_exists() and self.certificate_valid():
                logger.info("[SSL] Certificati SSL già presenti e validi")
                return True
            
            # Genera nuovo certificato
            logger.info("[SSL] Generazione nuovi certificati SSL...")
            self.generate_self_signed_cert(hostname)
            
            return True
            
        except Exception as e:
            logger.error(f"[SSL] Errore nella configurazione SSL: {e}")
            return False

# Importa ipaddress per la gestione degli indirizzi IP
import ipaddress

def create_ssl_manager():
    """Factory function per creare un SSLManager."""
    return SSLManager()

if __name__ == "__main__":
    # Test del modulo SSL
    logging.basicConfig(level=logging.INFO)
    
    print("[NETMASTER] Test del sistema SSL/TLS")
    print("-" * 50)
    
    ssl_manager = create_ssl_manager()
    
    # Configura SSL
    if ssl_manager.setup_ssl():
        print("[OK] SSL configurato correttamente")
        
        # Test contesto server
        try:
            server_context = ssl_manager.get_ssl_context(check_hostname=False)
            print("[OK] Contesto SSL server creato")
        except Exception as e:
            print(f"[ERRORE] Contesto server: {e}")
        
        # Test contesto client
        try:
            client_context = ssl_manager.get_client_ssl_context(verify_cert=False)
            print("[OK] Contesto SSL client creato")
        except Exception as e:
            print(f"[ERRORE] Contesto client: {e}")
    else:
        print("[ERRORE] Configurazione SSL fallita")
