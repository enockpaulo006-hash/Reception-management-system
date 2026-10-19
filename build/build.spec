# Build with: pyinstaller --noconfirm --clean build\build.spec
import os

from PyInstaller.utils.hooks import collect_data_files, collect_submodules


PROJECT_ROOT = os.path.abspath(os.path.join(SPECDIR, ".."))
ICON_PATH = os.path.join(SPECDIR, "app.ico")

# Templates, static assets, migrations, and management commands must be present
# in the frozen one-directory application.
datas = (
    collect_data_files(
        "reception",
        includes=["templates/**/*", "static/**/*", "migrations/*.py", "management/**/*.py"],
    )
    + collect_data_files("clinic", includes=["*.py"])
)

hiddenimports = (
    collect_submodules("clinic")
    + collect_submodules("reception")
    + [
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        "django.contrib.auth.backends",
        "django.contrib.auth.hashers",
        "django.contrib.auth.management.commands.createsuperuser",
        "django.contrib.sessions.middleware",
        "django.contrib.messages.middleware",
        "django.core.management.commands.collectstatic",
        "django.core.management.commands.migrate",
        "reception.management.commands.reset_password",
        "reception.management.commands.setup_clinic",
        "reception.middleware",
        "reception.context_processors",
        "reception.signals",
        "whitenoise.middleware",
        "waitress",
    ]
)

a = Analysis(
    [os.path.join(PROJECT_ROOT, "launcher.py")],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="ClinicReception",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=ICON_PATH if os.path.exists(ICON_PATH) else None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name="ClinicReception",
)
