#!/usr/bin/env python3
"""
NetMaster Test Runner
Script principale per eseguire tutti i test automatizzati
"""

import sys
import os
import time
import argparse
from datetime import datetime

# Aggiungi il path del progetto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_banner():
    """Stampa il banner di avvio"""
    print("\n" + "="*90)
    print("[TEST] NETMASTER AUTOMATED TEST SUITE")
    print("="*90)
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Directory: {os.getcwd()}")
    print("="*90)

def run_api_tests():
    """Esegue i test delle API"""
    print("\n[API] ESECUZIONE TEST API")
    print("-" * 50)
    
    try:
        from tests.test_api import run_test_suite
        success = run_test_suite()
        return success
    except ImportError as e:
        print(f"[ERROR] Errore importazione test API: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Errore esecuzione test API: {e}")
        return False

def run_integration_tests():
    """Esegue i test di integrazione"""
    print("\n[INTEGRATION] ESECUZIONE TEST INTEGRAZIONE")
    print("-" * 50)
    
    try:
        from tests.test_integration import run_integration_tests
        success = run_integration_tests()
        return success
    except ImportError as e:
        print(f"[ERROR] Errore importazione test integrazione: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Errore esecuzione test integrazione: {e}")
        return False

def check_dependencies():
    """Verifica che tutte le dipendenze siano installate"""
    print("\n[CHECK] VERIFICA DIPENDENZE")
    print("-" * 30)
    
    required_modules = [
        'flask', 'requests', 'psutil', 'bcrypt', 
        'cryptography', 'yagmail', 'sqlite3'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"[OK] {module}")
        except ImportError:
            print(f"[MISSING] {module} - MANCANTE")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\n[WARNING] Moduli mancanti: {', '.join(missing_modules)}")
        print("[INFO] Installa con: pip install -r requirements.txt")
        return False
    
    print("\n[OK] Tutte le dipendenze sono installate")
    return True

def check_environment():
    """Verifica l'ambiente di test"""
    print("\n[ENV] VERIFICA AMBIENTE")
    print("-" * 25)
    
    # Verifica file di configurazione
    config_files = ['.env', 'config.json', 'database.db']
    
    for file in config_files:
        if os.path.exists(file):
            print(f"[OK] {file}")
        else:
            print(f"[INFO] {file} - Non trovato (potrebbe essere normale)")
    
    # Verifica directory tests
    if os.path.exists('tests'):
        print("[OK] Directory tests")
        
        test_files = ['test_api.py', 'test_integration.py']
        for test_file in test_files:
            test_path = os.path.join('tests', test_file)
            if os.path.exists(test_path):
                print(f"[OK] tests/{test_file}")
            else:
                print(f"[MISSING] tests/{test_file} - MANCANTE")
                return False
    else:
        print("[MISSING] Directory tests - MANCANTE")
        return False
    
    print("\n[OK] Ambiente di test configurato correttamente")
    return True

def generate_test_report(api_success, integration_success, start_time, end_time):
    """Genera un report dei test"""
    duration = end_time - start_time
    
    print("\n" + "="*90)
    print("[REPORT] REPORT FINALE TEST SUITE")
    print("="*90)
    
    print(f"Durata totale: {duration:.2f} secondi")
    print(f"Test API: {'SUCCESSO' if api_success else 'FALLITO'}")
    print(f"Test Integrazione: {'SUCCESSO' if integration_success else 'FALLITO'}")
    
    overall_success = api_success and integration_success
    
    if overall_success:
        print("\n[SUCCESS] TUTTI I TEST COMPLETATI CON SUCCESSO!")
        print("[INFO] Il sistema NetMaster è pronto per la produzione")
    else:
        print("\n[WARNING] ALCUNI TEST SONO FALLITI")
        print("[INFO] Revisione necessaria prima del deployment")
    
    # Salva report su file
    try:
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"NetMaster Test Report\n")
            f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Durata: {duration:.2f} secondi\n")
            f.write(f"Test API: {'SUCCESSO' if api_success else 'FALLITO'}\n")
            f.write(f"Test Integrazione: {'SUCCESSO' if integration_success else 'FALLITO'}\n")
            f.write(f"Risultato Generale: {'SUCCESSO' if overall_success else 'FALLITO'}\n")
        
        print(f"[INFO] Report salvato in: {report_file}")
        
    except Exception as e:
        print(f"[WARNING] Impossibile salvare report: {e}")
    
    return overall_success

def main():
    """Funzione principale"""
    parser = argparse.ArgumentParser(description='NetMaster Test Runner')
    parser.add_argument('--api-only', action='store_true', 
                       help='Esegui solo i test API')
    parser.add_argument('--integration-only', action='store_true', 
                       help='Esegui solo i test di integrazione')
    parser.add_argument('--skip-checks', action='store_true', 
                       help='Salta le verifiche preliminari')
    
    args = parser.parse_args()
    
    print_banner()
    
    start_time = time.time()
    
    # Verifiche preliminari
    if not args.skip_checks:
        if not check_dependencies():
            print("\n[ERROR] Verifiche dipendenze fallite")
            sys.exit(1)
        
        if not check_environment():
            print("\n[ERROR] Verifiche ambiente fallite")
            sys.exit(1)
    
    # Esecuzione test
    api_success = True
    integration_success = True
    
    if not args.integration_only:
        print("\n" + "[API]" * 15)
        api_success = run_api_tests()
        
        if not api_success:
            print("\n[WARNING] Test API falliti - continuando con integrazione...")
    
    if not args.api_only:
        print("\n" + "[INTEGRATION]" * 8)
        integration_success = run_integration_tests()
    
    end_time = time.time()
    
    # Genera report finale
    overall_success = generate_test_report(
        api_success, integration_success, start_time, end_time
    )
    
    # Exit code
    sys.exit(0 if overall_success else 1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[WARNING] Test interrotti dall'utente")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Errore critico: {e}")
        sys.exit(1)
