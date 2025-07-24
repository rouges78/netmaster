#!/usr/bin/env python3
"""
NetMaster Test Suite - API Testing
Test automatizzati per le API del server NetMaster
"""

import unittest
import json
import time
import requests
import threading
from unittest.mock import patch, MagicMock
import sys
import os

# Aggiungi il path del progetto per importare i moduli
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server_integrated
import database
import credentials

class TestNetMasterAPI(unittest.TestCase):
    """Test suite per le API del server NetMaster"""
    
    @classmethod
    def setUpClass(cls):
        """Setup iniziale per tutti i test"""
        print("\n" + "="*60)
        print("[TEST] NETMASTER API TEST SUITE")
        print("="*60)
        
        # Configura server di test
        cls.server_host = '127.0.0.1'
        cls.server_port = 5001  # Porta diversa per test
        cls.base_url = f'http://{cls.server_host}:{cls.server_port}'
        cls.auth = ('admin', 'password')
        
        # Avvia server in thread separato
        cls.start_test_server()
        
        # Aspetta che il server sia pronto
        cls.wait_for_server()
        
    @classmethod
    def start_test_server(cls):
        """Avvia il server di test in un thread separato"""
        def run_server():
            # Configura app Flask per test
            app = server_integrated.app
            app.config['TESTING'] = True
            app.config['DEBUG'] = False
            
            # Avvia server
            app.run(
                host=cls.server_host,
                port=cls.server_port,
                debug=False,
                threaded=True,
                use_reloader=False
            )
        
        cls.server_thread = threading.Thread(target=run_server, daemon=True)
        cls.server_thread.start()
        
    @classmethod
    def wait_for_server(cls):
        """Aspetta che il server sia pronto per i test"""
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                response = requests.get(f'{cls.base_url}/api/health', 
                                      auth=cls.auth, timeout=2)
                if response.status_code == 200:
                    print(f"[OK] Server di test pronto su {cls.base_url}")
                    return
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(1)
            
        raise Exception("[ERROR] Impossibile avviare il server di test")
    
    def setUp(self):
        """Setup per ogni singolo test"""
        self.headers = {'Content-Type': 'application/json'}
        
    def test_01_server_health(self):
        """Test endpoint /api/health"""
        print("\n[TEST] Server Health Check")
        
        response = requests.get(f'{self.base_url}/api/health', auth=self.auth)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('status', data)
        self.assertIn('timestamp', data)
        self.assertIn('version', data)
        self.assertEqual(data['status'], 'healthy')
        
        print("[OK] Health check completato con successo")
        
    def test_02_authentication_required(self):
        """Test che l'autenticazione sia richiesta"""
        print("\n[TEST] Autenticazione Richiesta")
        
        # Test senza autenticazione
        response = requests.get(f'{self.base_url}/api/stats')
        self.assertEqual(response.status_code, 401)
        
        # Test con credenziali errate
        response = requests.get(f'{self.base_url}/api/stats', 
                               auth=('wrong', 'credentials'))
        self.assertEqual(response.status_code, 401)
        
        print("[OK] Autenticazione funziona correttamente")
        
    def test_03_stats_endpoint(self):
        """Test endpoint /api/stats"""
        print("\n[TEST] Statistiche Sistema")
        
        response = requests.get(f'{self.base_url}/api/stats', auth=self.auth)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verifica struttura dati
        required_fields = ['total_agents', 'avg_cpu', 'avg_memory', 
                          'avg_disk', 'active_alerts']
        for field in required_fields:
            self.assertIn(field, data)
            self.assertIsInstance(data[field], (int, float))
            
        print(f"[OK] Statistiche: {data}")
        
    def test_04_realtime_endpoint(self):
        """Test endpoint /api/realtime"""
        print("\n[TEST] Dati Real-time")
        
        # Test con timespan diversi
        timespans = ['1h', '6h', '24h']
        
        for timespan in timespans:
            response = requests.get(f'{self.base_url}/api/realtime', 
                                   params={'timespan': timespan}, 
                                   auth=self.auth)
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            self.assertIsInstance(data, list)
            
            if data:  # Se ci sono dati
                sample = data[0]
                required_fields = ['timestamp', 'cpu', 'memory', 'disk']
                for field in required_fields:
                    self.assertIn(field, sample)
                    
        print(f"[OK] Dati real-time per tutti i timespan")
        
    def test_05_agents_endpoint(self):
        """Test endpoint /api/agents"""
        print("\n[TEST] Lista Agent")
        
        response = requests.get(f'{self.base_url}/api/agents', auth=self.auth)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIsInstance(data, list)
        
        if data:  # Se ci sono agent
            agent = data[0]
            required_fields = ['id', 'hostname', 'ip_address', 'status',
                              'cpu_percent', 'memory_percent', 'disk_percent']
            for field in required_fields:
                self.assertIn(field, agent)
                
        print(f"[OK] Lista agent: {len(data)} agent trovati")
        
    def test_06_alerts_endpoint(self):
        """Test endpoint /api/alerts"""
        print("\n[TEST] Sistema Avvisi")
        
        response = requests.get(f'{self.base_url}/api/alerts', auth=self.auth)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIsInstance(data, list)
        
        if data:  # Se ci sono avvisi
            alert = data[0]
            required_fields = ['id', 'type', 'severity', 'title', 
                              'message', 'timestamp', 'active']
            for field in required_fields:
                self.assertIn(field, alert)
                
        print(f"[OK] Sistema avvisi: {len(data)} avvisi trovati")
        
    def test_07_history_endpoint(self):
        """Test endpoint /api/history"""
        print("\n[TEST] Storico Dati")
        
        response = requests.get(f'{self.base_url}/api/history', auth=self.auth)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIsInstance(data, list)
        
        print(f"[OK] Storico dati: {len(data)} record trovati")
        
    def test_08_thresholds_get(self):
        """Test endpoint GET /api/thresholds"""
        print("\n[TEST] Recupero Soglie")
        
        response = requests.get(f'{self.base_url}/api/thresholds', auth=self.auth)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIsInstance(data, list)
        
        print(f"[OK] Soglie recuperate: {len(data)} soglie")
        
    def test_09_thresholds_post(self):
        """Test endpoint POST /api/thresholds"""
        print("\n[TEST] Salvataggio Soglie")
        
        test_thresholds = {
            '192.168.1.100': {
                'cpu': 80,
                'memory': 90,
                'disk': 95
            }
        }
        
        response = requests.post(f'{self.base_url}/api/thresholds',
                                json=test_thresholds,
                                auth=self.auth,
                                headers=self.headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('message', data)
        
        print("[OK] Soglie salvate con successo")
        
    def test_10_notifications_config(self):
        """Test endpoint /api/notifications/config"""
        print("\n[TEST] Configurazione Notifiche")
        
        # Test GET
        response = requests.get(f'{self.base_url}/api/notifications/config', 
                               auth=self.auth)
        self.assertEqual(response.status_code, 200)
        
        # Test POST
        test_config = {
            'type': 'email',
            'config': {
                'smtp_server': 'smtp.test.com',
                'smtp_port': 587,
                'username': 'test@test.com',
                'recipients': ['admin@test.com']
            },
            'enabled': True
        }
        
        response = requests.post(f'{self.base_url}/api/notifications/config',
                                json=test_config,
                                auth=self.auth,
                                headers=self.headers)
        
        self.assertEqual(response.status_code, 200)
        
        print("[OK] Configurazione notifiche testata")
        
    def test_11_rate_limiting(self):
        """Test rate limiting delle API"""
        print("\n[TEST] Rate Limiting")
        
        # Fai molte richieste rapide per testare il rate limiting
        responses = []
        for i in range(10):
            response = requests.get(f'{self.base_url}/api/stats', auth=self.auth)
            responses.append(response.status_code)
            
        # Verifica che la maggior parte delle richieste abbia successo
        success_count = sum(1 for status in responses if status == 200)
        self.assertGreater(success_count, 5)  # Almeno metà devono avere successo
        
        print(f"[OK] Rate limiting: {success_count}/10 richieste riuscite")
        
    def test_12_json_validation(self):
        """Test validazione input JSON"""
        print("\n[TEST] Validazione Input JSON")
        
        # Test con JSON malformato
        response = requests.post(f'{self.base_url}/api/thresholds',
                                data='{"invalid": json}',  # JSON malformato
                                auth=self.auth,
                                headers=self.headers)
        
        self.assertEqual(response.status_code, 400)
        
        print("[OK] Validazione JSON funziona correttamente")

class TestNetMasterDatabase(unittest.TestCase):
    """Test suite per il database NetMaster"""
    
    def setUp(self):
        """Setup per ogni test del database"""
        print("\n[TEST] Database Setup")
        
    def test_01_database_connection(self):
        """Test connessione al database"""
        print("\n[TEST] Connessione Database")
        
        try:
            conn = database.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            conn.close()
            
            self.assertEqual(result[0], 1)
            print("[OK] Connessione database OK")
            
        except Exception as e:
            self.fail(f"Errore connessione database: {e}")
            
    def test_02_database_tables(self):
        """Test esistenza tabelle database"""
        print("\n[TEST] Tabelle Database")
        
        try:
            conn = database.get_db_connection()
            cursor = conn.cursor()
            
            # Verifica esistenza tabelle principali
            tables = ['system_data', 'thresholds', 'notification_config']
            
            for table in tables:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                result = cursor.fetchone()
                self.assertIsNotNone(result, f"Tabella {table} non trovata")
                
            conn.close()
            print("[OK] Tutte le tabelle esistono")
            
        except Exception as e:
            self.fail(f"Errore verifica tabelle: {e}")

class TestNetMasterCredentials(unittest.TestCase):
    """Test suite per il sistema credenziali"""
    
    def test_01_credentials_loading(self):
        """Test caricamento credenziali"""
        print("\n[TEST] Caricamento Credenziali")
        
        try:
            username, password = credentials.get_credentials()
            password_hash = credentials.get_password_hash()
            
            self.assertIsNotNone(username)
            self.assertIsNotNone(password_hash)
            
            print(f"[OK] Credenziali caricate: {username}")
            
        except Exception as e:
            self.fail(f"Errore caricamento credenziali: {e}")
            
    def test_02_credentials_validation(self):
        """Test validazione credenziali"""
        print("\n[TEST] Validazione Credenziali")
        
        try:
            is_valid = credentials.validate_credentials()
            self.assertTrue(is_valid)
            
            print("[OK] Credenziali valide")
            
        except Exception as e:
            self.fail(f"Errore validazione credenziali: {e}")

def run_test_suite():
    """Esegue l'intera suite di test"""
    print("\n" + "="*80)
    print("[START] AVVIO NETMASTER TEST SUITE")
    print("="*80)
    
    # Crea test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Aggiungi test classes
    test_classes = [
        TestNetMasterAPI,
        TestNetMasterDatabase,
        TestNetMasterCredentials
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Esegui i test
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Risultati finali
    print("\n" + "="*80)
    print("[RESULTS] RISULTATI FINALI")
    print("="*80)
    print(f"[OK] Test eseguiti: {result.testsRun}")
    print(f"[FAIL] Fallimenti: {len(result.failures)}")
    print(f"[ERROR] Errori: {len(result.errors)}")
    
    if result.failures:
        print("\n[FAIL] FALLIMENTI:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n[ERROR] ERRORI:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun) * 100
    print(f"\n[RATE] Tasso di successo: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("[SUCCESS] SUITE DI TEST COMPLETATA CON SUCCESSO!")
    elif success_rate >= 70:
        print("[WARNING] Suite di test completata con alcuni problemi")
    else:
        print("[FAIL] Suite di test fallita - necessaria revisione")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_test_suite()
    sys.exit(0 if success else 1)
