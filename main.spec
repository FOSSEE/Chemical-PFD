# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src\\main\\python\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('src/main/resources/base/config', 'resources/base/config'), ('src/main/resources/base/svg', 'resources/base/svg'), ('src/main/resources/base/toolbar', 'resources/base/toolbar'), ('src/main/resources/base/app.qss', 'resources/base'), ('src/main/resources/grips', 'resources/grips'), ('Component_Details.csv', '.')],
    hiddenimports=[],
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
    name='main',
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
