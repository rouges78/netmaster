import sqlite3
import os
from datetime import datetime

print("\n=== Verifica dati nel database ===")

db_path = os.path.join('data', 'monitoring.db')
if not os.path.exists(db_path):
    print(f"Database non trovato: {db_path}")
    exit(1)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\nUltimi 5 record:")
    cursor.execute("""
        SELECT timestamp, agent_ip, cpu_usage, memory_usage, disk_usage 
        FROM system_data 
        ORDER BY timestamp DESC 
        LIMIT 5
    """)
    
    rows = cursor.fetchall()
    if not rows:
        print("Nessun dato trovato")
    else:
        for row in rows:
            print(f"\nTimestamp: {row[0]}")
            print(f"Agent IP: {row[1]}")
            print(f"CPU: {row[2]}%")
            print(f"Memory: {row[3]}%")
            print(f"Disk: {row[4]}%")
            
except Exception as e:
    print(f"Errore: {str(e)}")
finally:
    if conn:
        conn.close()

input("\nPremi INVIO per chiudere...")
