# -*- mode: python ; coding: utf-8 -*-

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
    [r'C:/Users/davide/Desktop/progetto-server/netmaster_auto_launcher.py'],
    pathex=[r'C:/Users/davide/Desktop/progetto-server'],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
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
