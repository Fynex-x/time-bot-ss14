# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['time.py'],
    pathex=[],
    binaries=[('C:\\Program Files\\Tesseract-OCR\\tesseract.exe', '.')],
    datas=[('C:\\Program Files\\Tesseract-OCR\\tessdata', 'tessdata')],
    hiddenimports=['pytesseract'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='time',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
