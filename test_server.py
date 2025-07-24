import requests
import json
import time
import os

def test_server():
    print("\n=== Test del server di monitoraggio ===")
    print(f"Directory corrente: {os.getcwd()}")
    print("\nFile presenti:")
    for file in os.listdir():
        print(f"- {file}")
    
    print("\nTest di connessione al server...")
    print("Tentativo di connessione a http://localhost:5000")
    
    try:
        print("\nTest 1: Verifica che il server sia in esecuzione")
        print("URL: http://localhost:5000/history")
        print("Invio richiesta...")
        response = requests.get(
            'http://localhost:5000/history',
            auth=('admin', 'password'),
            verify=False
        )
        print(f"Status code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
    except requests.exceptions.ConnectionError:
        print("ERRORE: Impossibile connettersi al server. Il server è in esecuzione?")
        return
    except Exception as e:
        print(f"ERRORE: {str(e)}")
        return
        
    try:
        test_data = {
            "cpu_usage": 50.0,
            "memory": 60.0,
            "disk": 70.0,
            "system": "Windows",
            "node": "TestPC",
            "release": "10",
            "version": "10.0.19041"
        }
        
        print("\nTest 2: Invio dati di test")
        print("URL: http://localhost:5000/report")
        print("Dati da inviare:")
        print(json.dumps(test_data, indent=2))
        print("\nInvio richiesta...")
        
        response = requests.post(
            'http://localhost:5000/report',
            auth=('admin', 'password'),
            json=test_data,
            verify=False
        )
        print(f"Status code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
    except Exception as e:
        print(f"ERRORE: {str(e)}")
        return
        
    print("\nTest completato!")

if __name__ == "__main__":
    try:
        test_server()
    except Exception as e:
        print(f"\nERRORE FATALE: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        input("\nPremi INVIO per chiudere...")
