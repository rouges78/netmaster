#!/usr/bin/env python3
"""
NetMaster Monitoring Suite - Build EXE
Script per creare eseguibile Windows standalone (.exe)
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

class NetMasterExeBuilder:
    """Builder per eseguibile NetMaster."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.build_dir = self.project_root / 'build_exe'
        self.dist_dir = self.project_root / 'dist'
        
    def clean_build_dirs(self):
        """Pulisce directory di build precedenti."""
        print("Pulizia directory build...")
        
        dirs_to_clean = [self.build_dir, self.dist_dir, 'build', '__pycache__']
        for dir_name in dirs_to_clean:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"Rimossa: {dir_name}")
    
    def create_exe_launcher(self):
        """Crea launcher principale per l'exe."""
        launcher_content = '''#!/usr/bin/env python3
"""
NetMaster Monitoring Suite - Launcher EXE
Launcher principale per eseguibile Windows
"""

import os
import sys
import logging
from pathlib import Path

# Aggiungi directory corrente al path per importazioni
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def setup_exe_environment():
    """Configura ambiente per eseguibile."""
    # Imposta directory di lavoro
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller bundle
        os.chdir(sys._MEIPASS)
    else:
        # Sviluppo
        os.chdir(current_dir)
    
    # Configura variabili d'ambiente se non presenti
    env_vars = {
        'NETMASTER_USERNAME': 'admin',
        'NETMASTER_PASSWORD_HASH': '$2b$12$H5DowkEAanaIQbXx2zFnhe9YAs64KYcdVPWu0a.9pbQp9mOhzo1dW',
        'USE_HTTPS': 'false',  # Disabilita HTTPS per semplicità
        'NETMASTER_HOST': '127.0.0.1',
        'NETMASTER_PORT': '5000',
        'LOG_LEVEL': 'INFO'
    }
    
    for key, value in env_vars.items():
        if key not in os.environ:
            os.environ[key] = value

def main():
    """Funzione principale launcher."""
    try:
        print("=" * 60)
        print("NetMaster Monitoring Suite - Eseguibile Windows")
        print("=" * 60)
        print("Avvio server NetMaster...")
        print("Dashboard disponibile su: http://127.0.0.1:5000")
        print("Credenziali: admin / password")
        print("=" * 60)
        
        # Setup ambiente
        setup_exe_environment()
        
        # Importa e avvia server
        from server_integrated import app
        
        # Configura Flask per produzione
        app.config['DEBUG'] = False
        app.config['TESTING'] = False
        
        # Avvia server
        print("Server NetMaster avviato!")
        print("Premi Ctrl+C per arrestare il server")
        
        app.run(
            host=os.getenv('NETMASTER_HOST', '127.0.0.1'),
            port=int(os.getenv('NETMASTER_PORT', 5000)),
            threaded=True,
            use_reloader=False
        )
        
    except KeyboardInterrupt:
        print("\\nServer arrestato dall'utente")
    except Exception as e:
        print(f"Errore avvio NetMaster: {e}")
        input("Premi Enter per chiudere...")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
        
        launcher_file = self.project_root / 'netmaster_launcher.py'
        launcher_file.write_text(launcher_content, encoding='utf-8')
        print(f"Launcher creato: {launcher_file}")
        
        return launcher_file
    
    def create_pyinstaller_spec(self, launcher_file):
        """Crea file .spec per PyInstaller."""
        # Converti percorsi in formato raw string per evitare problemi Unicode
        launcher_path = str(launcher_file).replace('\\', '/')
        project_path = str(self.project_root).replace('\\', '/')
        
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# File da includere
added_files = [
    ('static', 'static'),
    ('certificates', 'certificates'),
    ('.env', '.'),
    ('README.md', '.'),
    ('DASHBOARD_GUIDE.md', '.'),
]

# Moduli nascosti necessari
hidden_imports = [
    'flask',
    'bcrypt',
    'yagmail',
    'cryptography',
    'requests',
    'psutil',
    'sqlite3',
    'json',
    'logging',
    'threading',
    'datetime',
    'os',
    'sys',
    'pathlib'
]

a = Analysis(
    [r'{launcher_path}'],
    pathex=[r'{project_path}'],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='NetMaster',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
'''
        
        spec_file = self.project_root / 'netmaster.spec'
        spec_file.write_text(spec_content, encoding='utf-8')
        print(f"Spec file creato: {spec_file}")
        
        return spec_file
    
    def build_executable(self, spec_file):
        """Costruisce l'eseguibile usando PyInstaller."""
        print("Costruzione eseguibile NetMaster...")
        print("Questo potrebbe richiedere alcuni minuti...")
        
        # Comando PyInstaller
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--noconfirm',
            str(spec_file)
        ]
        
        print(f"Comando: {' '.join(cmd)}")
        
        # Esegui build
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Build completata con successo!")
            return True
        else:
            print(f"Errore build: {result.stderr}")
            return False
    
    def create_portable_package(self):
        """Crea pacchetto portable con l'exe."""
        print("Creazione pacchetto portable...")
        
        exe_file = self.dist_dir / 'NetMaster.exe'
        if not exe_file.exists():
            print("Errore: File NetMaster.exe non trovato!")
            return False
        
        # Crea directory pacchetto
        package_dir = self.project_root / 'NetMaster_Portable'
        package_dir.mkdir(exist_ok=True)
        
        # Copia exe
        shutil.copy2(exe_file, package_dir / 'NetMaster.exe')
        
        # Crea file di configurazione semplificato
        config_content = '''# NetMaster - Configurazione Semplificata
# Modifica questi valori se necessario

# Credenziali (default: admin/password)
NETMASTER_USERNAME=admin
NETMASTER_PASSWORD_HASH=$2b$12$H5DowkEAanaIQbXx2zFnhe9YAs64KYcdVPWu0a.9pbQp9mOhzo1dW

# Server
NETMASTER_HOST=127.0.0.1
NETMASTER_PORT=5000
USE_HTTPS=false

# Logging
LOG_LEVEL=INFO
'''
        
        (package_dir / 'config.txt').write_text(config_content, encoding='utf-8')
        
        # Crea README per l'exe
        readme_content = '''# NetMaster Monitoring Suite - Eseguibile Portable

## Come Usare NetMaster

1. **Avvio**: Doppio click su NetMaster.exe
2. **Dashboard**: Apri browser su http://127.0.0.1:5000
3. **Login**: admin / password
4. **Stop**: Premi Ctrl+C nella finestra console

## Caratteristiche

- ✅ Eseguibile standalone (non richiede Python)
- ✅ Dashboard web moderna
- ✅ Monitoraggio sistemi in tempo reale
- ✅ API REST complete
- ✅ Database SQLite integrato
- ✅ Sicurezza e autenticazione

## Configurazione

Modifica il file `config.txt` per personalizzare:
- Porta del server
- Credenziali di accesso
- Livello di logging

## Supporto

Per supporto tecnico consultare la documentazione completa
nel progetto NetMaster originale.

---
NetMaster Monitoring Suite - Versione Eseguibile
'''
        
        (package_dir / 'README.txt').write_text(readme_content, encoding='utf-8')
        
        print(f"Pacchetto portable creato: {package_dir}")
        return package_dir
    
    def build(self):
        """Esegue build completo dell'eseguibile."""
        try:
            print("NetMaster EXE Builder - Avvio build")
            print("=" * 50)
            
            # Step build
            self.clean_build_dirs()
            launcher_file = self.create_exe_launcher()
            spec_file = self.create_pyinstaller_spec(launcher_file)
            
            if self.build_executable(spec_file):
                package_dir = self.create_portable_package()
                
                print("=" * 50)
                print("BUILD COMPLETATA CON SUCCESSO!")
                print(f"Eseguibile: {package_dir / 'NetMaster.exe'}")
                print("Per avviare: Doppio click su NetMaster.exe")
                print("Dashboard: http://127.0.0.1:5000")
                print("Credenziali: admin / password")
                
                return True
            else:
                print("BUILD FALLITA!")
                return False
                
        except Exception as e:
            print(f"Errore build: {e}")
            return False

def main():
    """Funzione principale."""
    builder = NetMasterExeBuilder()
    success = builder.build()
    
    if not success:
        input("Premi Enter per chiudere...")
        sys.exit(1)

if __name__ == "__main__":
    main()
