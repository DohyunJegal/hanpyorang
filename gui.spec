# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

block_cipher = None

pythonnet_datas = collect_data_files('pythonnet')
pythonnet_bins = collect_dynamic_libs('pythonnet')
clr_loader_datas = collect_data_files('clr_loader')
clr_loader_bins = collect_dynamic_libs('clr_loader')

a = Analysis(
    ['gui.py'],
    pathex=['.', 'lib'],
    binaries=[
        ('lib/liblouis.dll', '.'),
    ] + pythonnet_bins + clr_loader_bins,
    datas=[
        ('lib/tables', 'lib/tables'),
        ('gui/ui',     'gui/ui'),
    ] + pythonnet_datas + clr_loader_datas,
    hiddenimports=[
        'louis',
        'core',
        'core.pdf_extractor',
        'core.braille_converter',
        'core.brf_formatter',
        'core.brf_decoder',
        'gui.api',
        'webview',
        'webview.platforms.winforms',
        'clr',
        'pythonnet',
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
    name='pdf2brf',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='assets/icon.ico',
    disable_windowed_traceback=False,
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
    name='pdf2brf',
)
