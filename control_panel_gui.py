import tkinter as tk
from tkinter import messagebox
import subprocess
import os
from tkinter import ttk
from tkinter import filedialog
import threading
import time
import socket
import json

import sqlite3
import psutil  # per il controllo delle soglie di sistema
import shutil
from pathlib import Path



# Lista dei dispositivi connessi
devices = {}  # Chiave: indirizzo IP, Valore: informazioni sul dispositivo

# Variabile globale per memorizzare il percorso della cartella di rete condivisa
shared_network_folder = ""

# Funzione per ottenere l'indirizzo IP locale del server
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Tenta di connettersi per ottenere l'IP locale
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception as e:
        ip = "127.0.0.1"  # Fallback su localhost in caso di problemi
    finally:
        s.close()
    return ip



# Funzione per creare l'eseguibile dell'agent in un thread separato
def create_executable():
    def run_create():
        try:
            agent_path = os.path.abspath("agent.py")
            if not os.path.exists(agent_path):
                messagebox.showerror("Errore", f"File agent.py non trovato nel percorso: {agent_path}")
                update_log(f"File agent.py non trovato. Impossibile creare l'eseguibile.")
                return

            # Usa PyInstaller per creare l'eseguibile
            command = [
                "python", "-m", "PyInstaller", "--onefile", "--noconsole", agent_path
            ]
            update_log("Creazione dell'eseguibile dell'agent in corso...")
            
            # Esegui PyInstaller e cattura l'output
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            
            # Decodifica l'output
            stdout = stdout.decode()
            stderr = stderr.decode()

            # Controlla se ci sono stati errori
            if process.returncode != 0:
                error_message = f"Errore durante la creazione dell'eseguibile:\n{stderr}"
                messagebox.showerror("Errore", error_message)
                update_log(error_message)
                return

            success_message = "Eseguibile creato con successo. Troverai il file nella cartella dist."
            messagebox.showinfo("Info", success_message)
            update_log(success_message)

            # Automatizza la distribuzione dell'eseguibile
            distribute_executable()
        except FileNotFoundError:
            error_message = "PyInstaller non è stato trovato. Assicurati che sia installato."
            messagebox.showerror("Errore", error_message)
            update_log(error_message)

    threading.Thread(target=run_create, daemon=True).start()

# Funzione per selezionare la cartella di rete condivisa
def select_shared_folder():
    global shared_network_folder
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        shared_network_folder = folder_selected
        update_log(f"Cartella di rete selezionata: {shared_network_folder}")

# Funzione per distribuire automaticamente l'eseguibile dell'agent
def distribute_executable():
    global shared_network_folder
    try:
        dist_folder = Path(os.getcwd()) / "dist"
        executable_path = dist_folder / "agent.exe"
        if not executable_path.exists():
            update_log("Errore: Eseguibile dell'agent non trovato nella cartella dist.")
            return

        # Controlla se la cartella di rete è stata selezionata
        if not shared_network_folder:
            update_log("Errore: Nessuna cartella di rete selezionata per la distribuzione.")
            return

        shared_folder = Path(shared_network_folder)
        
        # Verifica che la cartella di rete esista e sia accessibile
        if not shared_folder.exists():
            error_message = f"Errore: La cartella di rete '{shared_folder}' non esiste."
            messagebox.showerror("Errore", error_message)
            update_log(error_message)
            return

        if not os.access(shared_folder, os.W_OK):
            error_message = f"Errore: Non hai i permessi di scrittura per la cartella di rete '{shared_folder}'."
            messagebox.showerror("Errore", error_message)
            update_log(error_message)
            return

        # Copia l'eseguibile nella cartella condivisa
        shutil.copy(executable_path, shared_folder / "agent.exe")
        update_log(f"Eseguibile copiato nella cartella di rete: {shared_folder}")
    except Exception as e:
        error_message = f"Errore durante la distribuzione dell'eseguibile: {str(e)}"
        messagebox.showerror("Errore", error_message)
        update_log(error_message)

# Funzione per aggiornare il log del server in tempo reale
def update_server_log():
    log_file_path = 'server_gui_log.txt'
    last_position = 0
    while True:
        try:
            with open(log_file_path, 'r') as f:
                f.seek(last_position)
                new_lines = f.readlines()
                if new_lines:
                    for line in new_lines:
                        update_log(line.strip())
                last_position = f.tell()
        except FileNotFoundError:
            pass
        time.sleep(2)

# Crea la finestra GUI principale
root = tk.Tk()
root.title("NetMaster - Controller")
root.geometry("1200x800")
root.configure(bg='#2c3e50')

# Aggiungi il logo e l'intestazione
title_frame = tk.Frame(root, bg='#2c3e50')
title_frame.pack(pady=20)
header_label = tk.Label(title_frame, text="NetMaster", font=("Helvetica", 36, "bold"), fg='#ecf0f1', bg='#2c3e50')
header_label.pack()
subheader_label = tk.Label(title_frame, text="Gestione centralizzata della rete", font=("Helvetica", 18), fg='#bdc3c7', bg='#2c3e50')
subheader_label.pack()

# Frame per contenere i pulsanti
button_frame = tk.Frame(root, bg='#2c3e50')
button_frame.pack(pady=30)

# Stile personalizzato per i pulsanti
style = ttk.Style()
style.theme_use("clam")
style.configure('TButton', font=('Helvetica', 14), padding=10, background='#2980b9', foreground='#ffffff')
style.map('TButton', background=[('active', '#1abc9c')], foreground=[('active', '#ffffff')])



# Pulsante per creare l'eseguibile del client
btn_create_exe = ttk.Button(button_frame, text="Crea Eseguibile Agent", command=create_executable, style='TButton')
btn_create_exe.grid(row=1, column=0, padx=20, pady=15)

# Pulsante per selezionare la cartella di rete condivisa
btn_select_folder = ttk.Button(button_frame, text="Seleziona Cartella di Rete", command=select_shared_folder, style='TButton')
btn_select_folder.grid(row=2, column=0, padx=20, pady=15)

# Frame per il log e la visualizzazione dei dati
tab_control = ttk.Notebook(root)
log_tab = ttk.Frame(tab_control)
dashboard_tab = ttk.Frame(tab_control)
devices_tab = ttk.Frame(tab_control)

# Aggiungi i tab al controllo delle tab
tab_control.add(log_tab, text='Log del Server')
tab_control.add(dashboard_tab, text='Dashboard Monitoraggio')
tab_control.add(devices_tab, text='Dispositivi in Rete')
tab_control.pack(expand=1, fill='both', padx=10, pady=10)

# Widget per il log del server
log_text = tk.Text(log_tab, wrap='word', font=('Courier', 12), background='#ecf0f1', foreground='#2c3e50')
log_text.pack(expand=1, fill='both', padx=10, pady=10)

# Funzione per aggiornare il log
def update_log(output):
    log_text.insert(tk.END, output + "\n")
    log_text.see(tk.END)

# Dashboard per il monitoraggio in tempo reale dei dati ricevuti
dashboard_tree = ttk.Treeview(dashboard_tab, columns=("Parametro", "Valore"), show='headings')
dashboard_tree.heading("Parametro", text="Parametro")
dashboard_tree.heading("Valore", text="Valore")
dashboard_tree.pack(expand=1, fill='both', padx=10, pady=10)



# Lista dei dispositivi connessi nella tab "Dispositivi in Rete"
devices_tree = ttk.Treeview(devices_tab, columns=("Indirizzo IP", "Nome Host", "Stato"), show='headings')
devices_tree.heading("Indirizzo IP", text="Indirizzo IP")
devices_tree.heading("Nome Host", text="Nome Host")
devices_tree.heading("Stato", text="Stato")
devices_tree.pack(expand=1, fill='both', padx=10, pady=10)





# Funzione per recuperare e aggiornare i dati dal database
def fetch_and_update_data():
    db_path = os.path.join('data', 'monitoring.db')
    if not os.path.exists(db_path):
        update_log("Database non trovato. Assicurati che il server sia stato avviato almeno una volta.")
        return

    while True:
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Recupera l'ultimo record per ogni agent
            cursor.execute("""
                SELECT agent_ip, agent_name, cpu_usage, memory_usage, disk_usage, timestamp
                FROM system_data
                WHERE (agent_ip, timestamp) IN (
                    SELECT agent_ip, MAX(timestamp) 
                    FROM system_data 
                    GROUP BY agent_ip
                )
            """)
            latest_records = cursor.fetchall()
            conn.close()

            # Funzione per aggiornare la GUI nel thread principale
            def update_gui():
                # Pulisci le viste esistenti
                for item in devices_tree.get_children():
                    devices_tree.delete(item)
                for item in dashboard_tree.get_children():
                    dashboard_tree.delete(item)

                if not latest_records:
                    devices_tree.insert("", "end", values=("N/A", "Nessun agente connesso", "N/A"))
                else:
                    for record in latest_records:
                        ip, name, cpu, mem, disk, ts = record
                        status = "Connesso"
                        # Aggiungi alla lista dispositivi
                        devices_tree.insert("", "end", values=(ip, name, status))
                        
                        # Aggiungi i dati al dashboard (mostra solo il primo agente per semplicità)
                        if dashboard_tree.get_children() == (): # Mostra solo il primo
                            dashboard_tree.insert("", "end", values=("agent_ip", ip))
                            dashboard_tree.insert("", "end", values=("agent_name", name))
                            dashboard_tree.insert("", "end", values=("cpu_usage", f"{cpu}%"))
                            dashboard_tree.insert("", "end", values=("memory_usage", f"{mem}%"))
                            dashboard_tree.insert("", "end", values=("disk_usage", f"{disk}%"))
                            dashboard_tree.insert("", "end", values=("last_update", ts))

            # Esegui l'aggiornamento della GUI nel thread principale di Tkinter
            root.after(0, update_gui)

        except Exception as e:
            update_log(f"Errore durante l'aggiornamento dati: {e}")
        
        time.sleep(5) # Aggiorna ogni 5 secondi

# Avvia i thread per l'aggiornamento in tempo reale
threading.Thread(target=update_server_log, daemon=True).start()
threading.Thread(target=fetch_and_update_data, daemon=True).start()

# Esegui l'interfaccia grafica
root.mainloop()
