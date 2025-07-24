import requests
import json

print("\n=== Test semplice del server ===")

try:
    print("\nTest 1: GET /history")
    response = requests.get('http://localhost:5001/history', auth=('admin', 'password'))
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Errore: {str(e)}")

try:
    print("\nTest 2: POST /report")
    data = {
        "cpu_usage": 50.0,
        "memory": 60.0,
        "disk": 70.0,
        "system": "Windows",
        "node": "TestPC",
        "release": "10",
        "version": "10.0.19041"
    }
    response = requests.post('http://localhost:5001/report', auth=('admin', 'password'), json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Errore: {str(e)}")

# input("\nPremi INVIO per chiudere...")
