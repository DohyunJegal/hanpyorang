# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['gui.py'],
    pathex=['.', 'lib'],   # lib/louis.py를 모듈로 인식
    binaries=[
        ('lib/liblouis.dll', '.'),
    ],
    datas=[
        ('lib/tables', 'lib/tables'),
        ('gui/ui',     'gui/ui'),
    ],
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
