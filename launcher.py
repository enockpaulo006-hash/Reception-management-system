"""Local packaged-app entry point for password recovery."""
import argparse
import os
import sqlite3
import subprocess
import sys
import webbrowser
from pathlib import Path


def create_backup():
    from django.db import connection
    from django.utils import timezone

    backup_directory = Path(r"C:\ProgramData\ClinicReception\backup")
    backup_directory.mkdir(parents=True, exist_ok=True)
    backup_path = backup_directory / f"clinic-{timezone.now():%Y%m%d-%H%M%S}.sqlite3"

    connection.ensure_connection()
    destination = sqlite3.connect(backup_path)
    try:
        connection.connection.backup(destination)
    finally:
        destination.close()
    (backup_directory / "last_backup.txt").write_text(timezone.now().isoformat(), encoding="utf-8")


def run_application():
    from django.core.management import call_command
    from waitress import serve

    call_command("migrate", interactive=False, verbosity=0)
    call_command("setup_clinic", verbosity=0)
    url = "http://127.0.0.1:8000/"
    edge_paths = (
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Microsoft\Edge\Application\msedge.exe",
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Microsoft\Edge\Application\msedge.exe",
    )
    for edge_path in edge_paths:
        if edge_path.exists():
            subprocess.Popen([str(edge_path), f"--app={url}"])
            break
    else:
        webbrowser.open(url)
    serve("clinic.wsgi:application", host="127.0.0.1", port=8000)


def main():
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--reset-password", metavar="USERNAME")
    action.add_argument("--backup", action="store_true")
    args = parser.parse_args()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "clinic.settings")
    if getattr(sys, "frozen", False):
        os.environ.setdefault("CLINIC_PRODUCTION", "1")
    import django

    django.setup()
    if args.backup:
        create_backup()
        return

    if args.reset_password:
        from reception.password_recovery import reset_password

        reset_password(args.reset_password)
        print("Password reset complete.")
        return

    run_application()


if __name__ == "__main__":
    main()
