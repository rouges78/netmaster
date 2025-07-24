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
    [r'C:/Users/davide/Desktop/progetto-server/netmaster_launcher.py'],
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
