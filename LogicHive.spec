# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# Collect data files for critical dependencies
datas = collect_data_files('fastembed')
datas += collect_data_files('mcp')

a = Analysis(
    ['backend/edge/mcp_server.py'],
    pathex=['backend'],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'duckdb',
        'fastembed',
        'google-genai',
        'uvicorn',
        'mcp',
        'edge.orchestrator',
        'core.database',
        'core.embedding',
        'core.quality',
        'core.security',
        'core.sanitizer',
        'edge.vector_db',
        'edge.cache',
        'edge.worker',
    ],
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
    [],
    exclude_binaries=True,
    name='LogicHive',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LogicHive',
)
