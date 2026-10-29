
# Build with:
# pyinstaller --noconfirm --clean build\build.spec

import os

from PyInstaller.utils.hooks import collect_data_files, collect_submodules


# =========================================================
# 1. PROJECT PATHS
# =========================================================

PROJECT_ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
ICON_PATH = os.path.join(SPECPATH, "app.ico")

STATIC_SOURCE = os.path.join(PROJECT_ROOT, "static")
STATICFILES_SOURCE = os.path.join(PROJECT_ROOT, "staticfiles")


# =========================================================
# 2. APPLICATION DATA FILES
# =========================================================

datas = (
    collect_data_files(
        "reception",
        includes=[
            "templates/**/*",
            "static/**/*",
            "migrations/*.py",
            "management/**/*.py",
        ],
    )
    + collect_data_files("clinic", includes=["*.py"])
)


# =========================================================
# 3. INCLUDE ORIGINAL STATIC FILES
# =========================================================

if not os.path.isdir(STATIC_SOURCE):
    raise FileNotFoundError(
        f"Required static directory not found: {STATIC_SOURCE}"
    )

for root, _, filenames in os.walk(STATIC_SOURCE):
    for filename in filenames:
        source = os.path.join(root, filename)
        relative_directory = os.path.relpath(root, STATIC_SOURCE)

        destination = (
            "static"
            if relative_directory == "."
            else os.path.join("static", relative_directory)
        )

        datas.append((source, destination))


# =========================================================
# 4. INCLUDE COLLECTED STATIC FILES AND MANIFEST
# =========================================================

MANIFEST_PATH = os.path.join(
    STATICFILES_SOURCE,
    "staticfiles.json",
)

if not os.path.isfile(MANIFEST_PATH):
    raise FileNotFoundError(
        "Django's staticfiles.json manifest is missing. "
        "Run manage.py collectstatic --noinput first."
    )

for root, _, filenames in os.walk(STATICFILES_SOURCE):
    for filename in filenames:
        source = os.path.join(root, filename)
        relative_path = os.path.relpath(source, STATICFILES_SOURCE)
        destination = os.path.join(
            "staticfiles",
            os.path.dirname(relative_path),
        )

        datas.append((source, destination))


# =========================================================
# 5. HIDDEN IMPORTS
# =========================================================

hiddenimports = (
    collect_submodules("clinic")
    + collect_submodules("reception")
    + collect_submodules("whitenoise")
    + collect_submodules("waitress")
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
        "whitenoise.storage",
        "whitenoise.storage.compressed",
        "whitenoise.storage.manifest",
    ]
)


# =========================================================
# 6. PYINSTALLER ANALYSIS
# =========================================================

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


# =========================================================
# 7. PYTHON BYTECODE ARCHIVE
# =========================================================

pyz = PYZ(a.pure)


# =========================================================
# 8. EXECUTABLE
# =========================================================

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


# =========================================================
# 9. COLLECT DISTRIBUTION FILES
# =========================================================

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name="ClinicReception",
)
