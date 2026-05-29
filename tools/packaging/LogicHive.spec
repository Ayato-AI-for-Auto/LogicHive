# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import copy_metadata, collect_data_files

block_cipher = None

# Reliable way to get script directory
script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

# Ensure the project root is in the path so 'src' is resolvable
project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'src'))

# Common data and metadata
common_datas = copy_metadata('fastmcp') + copy_metadata('google-genai') + copy_metadata('mcp') + copy_metadata('flet') + copy_metadata('flet_desktop') + collect_data_files('flet')
common_hiddenimports = [
    'fastmcp',
    'google.genai',
    'google.genai.types',
    'google',
    'aiosqlite',
    'numpy',
    'faiss',
    'radon',
    'sqlite3',
    'psutil',
    'flet',
    'flet_desktop',
    'flet_runtime'
]

# --- 1. Engine Binary (Hub) ---
a_hub = Analysis(
    [os.path.join(project_root, 'src', 'mcp_server.py')],
    pathex=[os.path.join(project_root, 'src')],
    binaries=[],
    datas=common_datas,
    hiddenimports=common_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz_hub = PYZ(a_hub.pure, a_hub.zipped_data, cipher=block_cipher)

exe_hub = EXE(
    pyz_hub,
    a_hub.scripts,
    a_hub.binaries,
    a_hub.zipfiles,
    a_hub.datas,
    [],
    name='logichive-hub',
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

# --- 2. Control Binary (Settings GUI) ---
a_settings = Analysis(
    [os.path.join(project_root, 'src', 'settings_ui.py')],
    pathex=[os.path.join(project_root, 'src')],
    binaries=[],
    datas=common_datas,
    hiddenimports=common_hiddenimports + ['flet.canvas', 'flet.charts', 'flet.svg'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz_settings = PYZ(a_settings.pure, a_settings.zipped_data, cipher=block_cipher)

exe_settings = EXE(
    pyz_settings,
    a_settings.scripts,
    a_settings.binaries,
    a_settings.zipfiles,
    a_settings.datas,
    [],
    name='logichive-settings',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False, # GUI app, no console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
