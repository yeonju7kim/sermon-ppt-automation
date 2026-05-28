# PyInstaller spec — Windows 단일 GUI 실행파일 빌드용.
# 빌드: pyinstaller --clean ppt_automation.spec
# 결과: dist\SermonPPT.exe

# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        # 템플릿 PPT를 실행파일 내부에 번들. service.app_base_dir() 가 sys._MEIPASS 를 반환.
        ('sermon_template.pptx', '.'),
    ],
    hiddenimports=[
        # 동적 import되는 모듈이 누락되지 않도록 명시
        'docx',
        'lxml._elementpath',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 용량 줄이기 위한 미사용 모듈 제외
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
    ],
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
    name='SermonPPT',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,           # GUI 앱이므로 콘솔 창 안 띄움
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,               # 아이콘 추가 시 'app.ico' 로 변경
)
