# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None

# Ensure the project root is in the path so 'src' is resolvable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

a = Analysis(
    [os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'mcp_server.py'))],
    pathex=[os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))],
    binaries=[],
    datas=[],
    hiddenimports=[
        'fastmcp',
        'google-genai',
        'aiosqlite',
        'numpy',
        'faiss',
        'radon',
        'sqlite3'
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='LogicHive-MCP',
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
)
