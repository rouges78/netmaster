#!/usr/bin/env python3
"""
NetMaster Monitoring Suite - Build EXE Automatico
Script per creare eseguibile Windows completamente automatico
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

class NetMasterAutoExeBuilder:
    """Builder per eseguibile NetMaster automatico."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.build_dir = self.project_root / 'build_auto_exe'
        self.dist_dir = self.project_root / 'dist'
        
    def clean_build_dirs(self):
        """Pulisce directory di build precedenti."""
        print("Pulizia directory build automatico...")
        
        dirs_to_clean = [self.build_dir, self.dist_dir, 'build', '__pycache__']
        for dir_name in dirs_to_clean:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"Rimossa: {dir_name}")
    
    def create_pyinstaller_spec_auto(self):
        """Crea file .spec per eseguibile automatico."""
        launcher_path = str(self.project_root / 'netmaster_auto_launcher.py').replace('\\', '/')
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

# Moduli nascosti necessari per GUI e automazione
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
    'pathlib',
    'webbrowser',
    'tkinter',
    'tkinter.messagebox',
    'socket',
    'ctypes'
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
    name='NetMaster_Auto',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # IMPORTANTE: Nessuna console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
'''
        
        spec_file = self.project_root / 'netmaster_auto.spec'
        spec_file.write_text(spec_content, encoding='utf-8')
        print(f"Spec file automatico creato: {spec_file}")
        
        return spec_file
    
    def build_executable(self, spec_file):
        """Costruisce l'eseguibile usando PyInstaller."""
        print("Costruzione eseguibile NetMaster automatico...")
        print("Questo potrebbe richiedere alcuni minuti...")
        
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--noconfirm',
            str(spec_file)
        ]
        
        print(f"Comando: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Build automatico completata con successo!")
            return True
        else:
            print(f"Errore build: {result.stderr}")
            return False
    
    def create_auto_package(self):
        """Crea pacchetto automatico."""
        print("Creazione pacchetto automatico...")
        
        exe_file = self.dist_dir / 'NetMaster_Auto.exe'
        if not exe_file.exists():
            print("Errore: File NetMaster_Auto.exe non trovato!")
            return False
        
        # Crea directory pacchetto
        package_dir = self.project_root / 'NetMaster_Automatico'
        package_dir.mkdir(exist_ok=True)
        
        # Copia exe
        shutil.copy2(exe_file, package_dir / 'NetMaster.exe')
        
        # Crea README automatico
        readme_content = '''# NetMaster Monitoring Suite - Versione Automatica

## 🚀 Avvio Completamente Automatico

### Come Usare:
1. **Doppio click** su NetMaster.exe
2. Il sistema si avvia **automaticamente**
3. Il **browser si apre** automaticamente sulla dashboard
4. **Login automatico**: admin / password

### ✨ Caratteristiche Automatiche:
- ✅ **Zero configurazione** - Funziona immediatamente
- ✅ **Avvio trasparente** - Nessuna finestra console
- ✅ **Browser automatico** - Si apre da solo
- ✅ **Porta automatica** - Trova automaticamente una porta libera
- ✅ **Notifiche GUI** - Messaggi di stato eleganti

### 🎯 Funzionalità Complete:
- ✅ Dashboard web moderna e responsive
- ✅ Monitoraggio sistemi in tempo reale
- ✅ Grafici interattivi Chart.js
- ✅ API REST complete
- ✅ Database SQLite integrato
- ✅ Sicurezza e autenticazione

### 🔧 Controllo Sistema:
- **Dashboard**: http://127.0.0.1:5000 (o porta automatica)
- **Credenziali**: admin / password
- **Arresto**: Chiudi browser e termina processo dal Task Manager

### 💡 Note:
- Il programma gira in background senza finestre
- Riceverai una notifica quando è pronto
- Il browser si apre automaticamente
- Completamente standalone (non richiede Python)

---
NetMaster Monitoring Suite - Versione Automatica
Pronto per l'uso immediato!
'''
        
        (package_dir / 'README.txt').write_text(readme_content, encoding='utf-8')
        
        # Crea file di informazioni rapide
        quick_info = '''NETMASTER - AVVIO RAPIDO

1. Doppio click su NetMaster.exe
2. Attendi la notifica di avvio
3. Il browser si apre automaticamente
4. Login: admin / password

Tutto automatico!
'''
        
        (package_dir / 'AVVIO_RAPIDO.txt').write_text(quick_info, encoding='utf-8')
        
        print(f"Pacchetto automatico creato: {package_dir}")
        return package_dir
    
    def build(self):
        """Esegue build completo dell'eseguibile automatico."""
        try:
            print("NetMaster Auto EXE Builder - Avvio build automatico")
            print("=" * 60)
            
            self.clean_build_dirs()
            spec_file = self.create_pyinstaller_spec_auto()
            
            if self.build_executable(spec_file):
                package_dir = self.create_auto_package()
                
                print("=" * 60)
                print("BUILD AUTOMATICO COMPLETATO CON SUCCESSO!")
                print(f"Eseguibile: {package_dir / 'NetMaster.exe'}")
                print("CARATTERISTICHE AUTOMATICHE:")
                print("✅ Avvio trasparente (nessuna console)")
                print("✅ Browser si apre automaticamente")
                print("✅ Notifiche GUI eleganti")
                print("✅ Zero configurazione richiesta")
                print("✅ Completamente standalone")
                print("")
                print("Per usare: Doppio click su NetMaster.exe")
                print("Dashboard: http://127.0.0.1:5000")
                print("Credenziali: admin / password")
                
                return True
            else:
                print("BUILD AUTOMATICO FALLITO!")
                return False
                
        except Exception as e:
            print(f"Errore build automatico: {e}")
            return False

def main():
    """Funzione principale."""
    builder = NetMasterAutoExeBuilder()
    success = builder.build()
    
    if not success:
        input("Premi Enter per chiudere...")
        sys.exit(1)

if __name__ == "__main__":
    main()
