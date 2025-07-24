#!/usr/bin/env python3
"""
NetMaster Monitoring Suite - Launcher Automatico
Avvio completamente automatico con apertura browser e system tray
"""

import os
import sys
import time
import threading
import webbrowser
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import logging

# Disabilita logging verbose per interfaccia pulita
logging.getLogger('werkzeug').setLevel(logging.ERROR)

class NetMasterAutoLauncher:
    """Launcher automatico per NetMaster."""
    
    def __init__(self):
        self.server_thread = None
        self.server_running = False
        self.host = '127.0.0.1'
        self.port = 5000
        self.url = f'http://{self.host}:{self.port}'
        
        # Setup ambiente
        self.setup_environment()
        
    def setup_environment(self):
        """Configura ambiente automaticamente."""
        # Imposta directory di lavoro
        if hasattr(sys, '_MEIPASS'):
            os.chdir(sys._MEIPASS)
        else:
            os.chdir(Path(__file__).parent)
        
        # Variabili d'ambiente automatiche
        env_vars = {
            'NETMASTER_USERNAME': 'admin',
            'NETMASTER_PASSWORD_HASH': '$2b$12$H5DowkEAanaIQbXx2zFnhe9YAs64KYcdVPWu0a.9pbQp9mOhzo1dW',
            'USE_HTTPS': 'false',
            'NETMASTER_HOST': self.host,
            'NETMASTER_PORT': str(self.port),
            'LOG_LEVEL': 'ERROR'  # Minimal logging
        }
        
        for key, value in env_vars.items():
            os.environ[key] = value
    
    def check_port_available(self):
        """Verifica se la porta è disponibile."""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((self.host, self.port))
                return True
        except:
            return False
    
    def find_available_port(self):
        """Trova una porta disponibile."""
        for port in range(5000, 5100):
            try:
                import socket
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind((self.host, port))
                    self.port = port
                    self.url = f'http://{self.host}:{self.port}'
                    os.environ['NETMASTER_PORT'] = str(port)
                    return True
            except:
                continue
        return False
    
    def start_server(self):
        """Avvia server in thread separato."""
        try:
            # Verifica porta
            if not self.check_port_available():
                if not self.find_available_port():
                    self.show_error("Nessuna porta disponibile per NetMaster")
                    return False
            
            # Importa server
            from server_integrated import app
            
            # Configura Flask per produzione silenziosa
            app.config['DEBUG'] = False
            app.config['TESTING'] = False
            
            # Disabilita output Flask
            import logging
            log = logging.getLogger('werkzeug')
            log.setLevel(logging.ERROR)
            
            # Avvia server
            self.server_running = True
            app.run(
                host=self.host,
                port=self.port,
                threaded=True,
                use_reloader=False,
                debug=False
            )
            
        except Exception as e:
            self.server_running = False
            self.show_error(f"Errore avvio NetMaster: {e}")
    
    def wait_for_server(self, timeout=30):
        """Attende che il server sia pronto."""
        import requests
        
        for _ in range(timeout):
            try:
                response = requests.get(self.url, timeout=1)
                if response.status_code == 200:
                    return True
            except:
                pass
            time.sleep(1)
        return False
    
    def open_browser(self):
        """Apre automaticamente il browser."""
        try:
            # Attendi che il server sia pronto
            if self.wait_for_server():
                time.sleep(2)  # Pausa aggiuntiva per sicurezza
                webbrowser.open(self.url)
                return True
            else:
                self.show_error("Server NetMaster non risponde")
                return False
        except Exception as e:
            self.show_error(f"Errore apertura browser: {e}")
            return False
    
    def show_success_notification(self):
        """Mostra notifica di successo."""
        try:
            # Crea finestra di notifica temporanea
            root = tk.Tk()
            root.withdraw()  # Nascondi finestra principale
            
            # Notifica di successo
            messagebox.showinfo(
                "NetMaster Avviato", 
                f"NetMaster è stato avviato con successo!\\n\\n"
                f"Dashboard: {self.url}\\n"
                f"Credenziali: admin / password\\n\\n"
                f"Il browser si aprirà automaticamente."
            )
            
            root.destroy()
        except:
            pass  # Ignora errori GUI
    
    def show_error(self, message):
        """Mostra errore all'utente."""
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Errore NetMaster", message)
            root.destroy()
        except:
            print(f"Errore: {message}")
    
    def create_system_tray_info(self):
        """Crea file info per system tray."""
        try:
            info_content = f"""NetMaster Monitoring Suite - In Esecuzione

Dashboard: {self.url}
Credenziali: admin / password
Porta: {self.port}

Per arrestare NetMaster:
1. Chiudi la finestra del browser
2. Termina il processo NetMaster.exe dal Task Manager

NetMaster è ora in esecuzione in background.
"""
            
            info_file = Path("netmaster_info.txt")
            info_file.write_text(info_content, encoding='utf-8')
            
        except:
            pass  # Ignora errori
    
    def launch(self):
        """Avvio automatico completo."""
        try:
            # Avvia server in background
            self.server_thread = threading.Thread(target=self.start_server, daemon=True)
            self.server_thread.start()
            
            # Attendi avvio server
            time.sleep(3)
            
            if self.server_running:
                # Crea info system tray
                self.create_system_tray_info()
                
                # Mostra notifica successo
                self.show_success_notification()
                
                # Apri browser automaticamente
                if self.open_browser():
                    # Mantieni processo attivo
                    try:
                        while self.server_running:
                            time.sleep(10)
                    except KeyboardInterrupt:
                        pass
                else:
                    self.show_error("Impossibile aprire il browser automaticamente")
            else:
                self.show_error("Impossibile avviare il server NetMaster")
                
        except Exception as e:
            self.show_error(f"Errore launcher: {e}")

def main():
    """Funzione principale launcher automatico."""
    try:
        # Nascondi console se possibile
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
            except:
                pass
        
        # Avvia NetMaster automaticamente
        launcher = NetMasterAutoLauncher()
        launcher.launch()
        
    except Exception as e:
        # Fallback per errori critici
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Errore Critico NetMaster", f"Errore avvio: {e}")
            root.destroy()
        except:
            print(f"Errore critico: {e}")

if __name__ == "__main__":
    main()
