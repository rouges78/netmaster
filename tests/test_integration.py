#!/usr/bin/env python3
"""
NetMaster Integration Test Suite
Test end-to-end per l'intera pipeline NetMaster
"""

import unittest
import json
import time
import requests
import threading
import subprocess
import psutil
import sys
import os
from datetime import datetime

# Aggiungi il path del progetto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server_integrated
import agent
import database

class TestNetMasterIntegration(unittest.TestCase):
    """Test di integrazione end-to-end per NetMaster"""
    
    @classmethod
    def setUpClass(cls):
        """Setup per i test di integrazione"""
        print("\n" + "="*70)
        print("[INTEGRATION] NETMASTER INTEGRATION TEST SUITE")
        print("="*70)
        
        cls.server_host = '127.0.0.1'
        cls.server_port = 5002  # Porta diversa per test integrazione
        cls.base_url = f'http://{cls.server_host}:{cls.server_port}'
        cls.auth = ('admin', 'password')
        
        # Avvia server per test integrazione
        cls.start_integration_server()
        cls.wait_for_server()
        
    @classmethod
    def start_integration_server(cls):
        """Avvia server per test di integrazione"""
        def run_server():
            app = server_integrated.app
            app.config['TESTING'] = True
            app.config['DEBUG'] = False
            
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
        """Aspetta che il server sia pronto"""
        max_attempts = 20
        for attempt in range(max_attempts):
            try:
                response = requests.get(f'{cls.base_url}/api/health', 
                                      auth=cls.auth, timeout=2)
                if response.status_code == 200:
                    print(f"[OK] Server integrazione pronto su {cls.base_url}")
                    return
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)
            
        raise Exception("[ERROR] Server integrazione non disponibile")
    
    def test_01_server_agent_communication(self):
        """Test comunicazione completa server-agent"""
        print("\n[TEST] Comunicazione Server-Agent")
        
        # Simula invio dati da agent
        test_data = {
            'hostname': 'TEST-PC-INTEGRATION',
            'ip_address': '192.168.1.200',
            'timestamp': time.time(),
            'cpu_percent': 45.2,
            'memory_percent': 67.8,
            'disk_percent': 23.1,
            'cpu_count': 8,
            'memory_total': 16777216,  # 16GB in KB
            'disk_total': 1000000000,  # 1TB in KB
            'uptime': 86400,  # 1 giorno
            'processes': 156
        }
        
        # Invia dati al server
        response = requests.post(f'{self.base_url}/api/data',
                                json=test_data,
                                auth=self.auth,
                                headers={'Content-Type': 'application/json'})
        
        self.assertEqual(response.status_code, 200)
        
        # Verifica che i dati siano stati salvati
        time.sleep(1)  # Aspetta che i dati siano processati
        
        stats_response = requests.get(f'{self.base_url}/api/stats', auth=self.auth)
        self.assertEqual(stats_response.status_code, 200)
        
        agents_response = requests.get(f'{self.base_url}/api/agents', auth=self.auth)
        self.assertEqual(agents_response.status_code, 200)
        
        agents_data = agents_response.json()
        test_agent_found = any(agent['hostname'] == 'TEST-PC-INTEGRATION' 
                              for agent in agents_data)
        
        self.assertTrue(test_agent_found, "Agent di test non trovato nei dati")
        
        print("[OK] Comunicazione server-agent completata con successo")
        
    def test_02_dashboard_data_flow(self):
        """Test flusso dati dalla dashboard"""
        print("\n[TEST] Flusso Dati Dashboard")
        
        # Test tutti gli endpoint utilizzati dalla dashboard
        endpoints = [
            '/api/stats',
            '/api/realtime',
            '/api/agents',
            '/api/alerts',
            '/api/history',
            '/api/thresholds'
        ]
        
        for endpoint in endpoints:
            response = requests.get(f'{self.base_url}{endpoint}', auth=self.auth)
            self.assertEqual(response.status_code, 200, 
                           f"Endpoint {endpoint} fallito")
            
            # Verifica che la risposta sia JSON valido
            try:
                data = response.json()
                self.assertIsNotNone(data)
            except json.JSONDecodeError:
                self.fail(f"Endpoint {endpoint} non restituisce JSON valido")
                
        print("[OK] Tutti gli endpoint dashboard funzionanti")
        
    def test_03_threshold_alert_system(self):
        """Test sistema soglie e avvisi"""
        print("\n[TEST] Sistema Soglie e Avvisi")
        
        # Imposta soglie basse per test
        test_thresholds = {
            'TEST-PC-INTEGRATION': {
                'cpu': 40,      # Soglia bassa per triggerare avviso
                'memory': 60,   # Soglia bassa per triggerare avviso
                'disk': 90
            }
        }
        
        # Salva soglie
        response = requests.post(f'{self.base_url}/api/thresholds',
                                json=test_thresholds,
                                auth=self.auth,
                                headers={'Content-Type': 'application/json'})
        
        self.assertEqual(response.status_code, 200)
        
        # Invia dati che superano le soglie
        high_usage_data = {
            'hostname': 'TEST-PC-INTEGRATION',
            'ip_address': '192.168.1.200',
            'timestamp': time.time(),
            'cpu_percent': 85.5,  # Supera soglia CPU (40%)
            'memory_percent': 92.3,  # Supera soglia memoria (60%)
            'disk_percent': 25.1,
            'cpu_count': 8,
            'memory_total': 16777216,
            'disk_total': 1000000000,
            'uptime': 86400,
            'processes': 200
        }
        
        response = requests.post(f'{self.base_url}/api/data',
                                json=high_usage_data,
                                auth=self.auth,
                                headers={'Content-Type': 'application/json'})
        
        self.assertEqual(response.status_code, 200)
        
        # Aspetta che gli avvisi siano generati
        time.sleep(2)
        
        # Verifica che siano stati generati avvisi
        alerts_response = requests.get(f'{self.base_url}/api/alerts', auth=self.auth)
        self.assertEqual(alerts_response.status_code, 200)
        
        alerts_data = alerts_response.json()
        
        # Verifica che ci siano avvisi per CPU e memoria
        cpu_alert_found = any(alert['type'] == 'cpu' and 
                             alert['agent_hostname'] == 'TEST-PC-INTEGRATION'
                             for alert in alerts_data)
        
        memory_alert_found = any(alert['type'] == 'memory' and 
                                alert['agent_hostname'] == 'TEST-PC-INTEGRATION'
                                for alert in alerts_data)
        
        self.assertTrue(cpu_alert_found, "Avviso CPU non generato")
        self.assertTrue(memory_alert_found, "Avviso memoria non generato")
        
        print("[OK] Sistema soglie e avvisi funzionante")
        
    def test_04_data_persistence(self):
        """Test persistenza dati nel database"""
        print("\n[TEST] Persistenza Dati Database")
        
        # Invia dati di test
        test_data = {
            'hostname': 'TEST-PERSISTENCE',
            'ip_address': '192.168.1.201',
            'timestamp': time.time(),
            'cpu_percent': 33.3,
            'memory_percent': 44.4,
            'disk_percent': 55.5,
            'cpu_count': 4,
            'memory_total': 8388608,
            'disk_total': 500000000,
            'uptime': 43200,
            'processes': 89
        }
        
        response = requests.post(f'{self.base_url}/api/data',
                                json=test_data,
                                auth=self.auth,
                                headers={'Content-Type': 'application/json'})
        
        self.assertEqual(response.status_code, 200)
        
        # Aspetta che i dati siano salvati
        time.sleep(1)
        
        # Verifica che i dati siano nel database
        try:
            conn = database.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM system_data 
                WHERE hostname = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            """, ('TEST-PERSISTENCE',))
            
            result = cursor.fetchone()
            conn.close()
            
            self.assertIsNotNone(result, "Dati non trovati nel database")
            
            # Verifica che i dati salvati corrispondano
            self.assertEqual(result[1], 'TEST-PERSISTENCE')  # hostname
            self.assertEqual(result[2], '192.168.1.201')     # ip_address
            
        except Exception as e:
            self.fail(f"Errore verifica database: {e}")
            
        print("[OK] Persistenza dati database verificata")
        
    def test_05_api_security(self):
        """Test sicurezza API"""
        print("\n[TEST] Sicurezza API")
        
        # Test autenticazione richiesta
        response = requests.get(f'{self.base_url}/api/stats')
        self.assertEqual(response.status_code, 401)
        
        # Test credenziali errate
        response = requests.get(f'{self.base_url}/api/stats', 
                               auth=('wrong', 'credentials'))
        self.assertEqual(response.status_code, 401)
        
        # Test input validation
        invalid_data = {
            'hostname': '<script>alert("xss")</script>',  # Tentativo XSS
            'cpu_percent': 'invalid_number',              # Tipo errato
            'timestamp': 'not_a_timestamp'                # Timestamp invalido
        }
        
        response = requests.post(f'{self.base_url}/api/data',
                                json=invalid_data,
                                auth=self.auth,
                                headers={'Content-Type': 'application/json'})
        
        # Dovrebbe essere rifiutato (400 o 422)
        self.assertIn(response.status_code, [400, 422])
        
        print("[OK] Sicurezza API verificata")
        
    def test_06_performance_load(self):
        """Test performance sotto carico"""
        print("\n[TEST] Performance Sotto Carico")
        
        # Invia molte richieste simultanee
        import concurrent.futures
        
        def send_request(i):
            test_data = {
                'hostname': f'LOAD-TEST-{i}',
                'ip_address': f'192.168.1.{100 + (i % 50)}',
                'timestamp': time.time(),
                'cpu_percent': 20 + (i % 60),
                'memory_percent': 30 + (i % 50),
                'disk_percent': 15 + (i % 30),
                'cpu_count': 4,
                'memory_total': 8388608,
                'disk_total': 500000000,
                'uptime': 3600 * i,
                'processes': 50 + (i % 100)
            }
            
            response = requests.post(f'{self.base_url}/api/data',
                                    json=test_data,
                                    auth=self.auth,
                                    headers={'Content-Type': 'application/json'},
                                    timeout=10)
            return response.status_code
        
        # Test con 20 richieste simultanee
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(send_request, i) for i in range(20)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Verifica che la maggior parte delle richieste abbia successo
        success_count = sum(1 for status in results if status == 200)
        success_rate = (success_count / len(results)) * 100
        
        self.assertGreater(success_rate, 80, "Tasso di successo troppo basso sotto carico")
        self.assertLess(duration, 30, "Tempo di risposta troppo alto sotto carico")
        
        print(f"[OK] Performance: {success_rate:.1f}% successo in {duration:.2f}s")
        
    def test_07_system_monitoring_cycle(self):
        """Test ciclo completo di monitoraggio"""
        print("\n[TEST] Ciclo Completo Monitoraggio")
        
        # Simula un ciclo completo di monitoraggio
        cycle_data = []
        
        for i in range(5):
            # Simula dati che cambiano nel tempo
            data = {
                'hostname': 'CYCLE-TEST-PC',
                'ip_address': '192.168.1.210',
                'timestamp': time.time(),
                'cpu_percent': 30 + (i * 10),  # CPU che aumenta
                'memory_percent': 40 + (i * 5),  # Memoria che aumenta
                'disk_percent': 20 + i,
                'cpu_count': 8,
                'memory_total': 16777216,
                'disk_total': 1000000000,
                'uptime': 86400 + (i * 3600),  # Uptime che aumenta
                'processes': 100 + (i * 10)
            }
            
            response = requests.post(f'{self.base_url}/api/data',
                                    json=data,
                                    auth=self.auth,
                                    headers={'Content-Type': 'application/json'})
            
            self.assertEqual(response.status_code, 200)
            cycle_data.append(data)
            
            time.sleep(0.5)  # Pausa tra invii
        
        # Verifica che i dati storici siano disponibili
        history_response = requests.get(f'{self.base_url}/api/history', 
                                       auth=self.auth)
        self.assertEqual(history_response.status_code, 200)
        
        history_data = history_response.json()
        
        # Verifica che ci siano dati per il nostro PC di test
        cycle_records = [record for record in history_data 
                        if record.get('hostname') == 'CYCLE-TEST-PC']
        
        self.assertGreater(len(cycle_records), 0, 
                          "Nessun record storico trovato per il ciclo di test")
        
        print(f"[OK] Ciclo monitoraggio: {len(cycle_records)} record storici")

def run_integration_tests():
    """Esegue i test di integrazione"""
    print("\n" + "="*80)
    print("[START] AVVIO NETMASTER INTEGRATION TEST SUITE")
    print("="*80)
    
    # Crea test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestNetMasterIntegration)
    
    # Esegui i test
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Risultati finali
    print("\n" + "="*80)
    print("[RESULTS] RISULTATI INTEGRAZIONE")
    print("="*80)
    print(f"[OK] Test eseguiti: {result.testsRun}")
    print(f"[FAIL] Fallimenti: {len(result.failures)}")
    print(f"[ERROR] Errori: {len(result.errors)}")
    
    if result.failures:
        print("\n[FAIL] FALLIMENTI:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print("\n[ERROR] ERRORI:")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun) * 100
    print(f"\n[RATE] Tasso di successo integrazione: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("[SUCCESS] TEST DI INTEGRAZIONE COMPLETATI CON SUCCESSO!")
    elif success_rate >= 70:
        print("[WARNING] Test di integrazione completati con alcuni problemi")
    else:
        print("[FAIL] Test di integrazione falliti - necessaria revisione")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_integration_tests()
    sys.exit(0 if success else 1)
