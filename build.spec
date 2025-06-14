# -*- mode: python -*-
from PyInstaller.utils.hooks import collect_data_files
import os

block_cipher = None

a = Analysis(
    ['front/Main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('front/logo.png', 'front'),  # Inclui a logo
        ('front/logo.ico', '.'),      # Inclui o ícone (COM VÍRGULA)
        ('activities', 'activities'), # Pasta de atividades (COM VÍRGULA)
        ('submissions', 'submissions') # Pasta de submissões
    ],
    hiddenimports=[],
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
    name='SistemaAcademico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon=os.path.join('front', 'logo.ico'),  # Caminho relativo para o ícone
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    onefile=True
)