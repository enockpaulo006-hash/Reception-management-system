You are helping me build "Clinic Reception", a small offline Windows app for a clinic.

PURPOSE: control revenue so money cannot disappear. It is NOT a hospital management system.
No patient history, no doctor/lab modules, no insurance, no network, no online access.

CONTEXT: one Windows PC, one receptionist, about 10 patients/day, cash only,
internal receipts (not TRA/EFD). The owner audits locally.

STACK: Python 3.13, Django 6.x, SQLite (WAL mode), Django templates + plain HTML/CSS/JS,
WhiteNoise, Waitress, openpyxl. No React, no REST API, no Docker, no GUI packages.
The app runs on 127.0.0.1 and is shown in an Edge window in --app mode.

ALREADY DONE: Django project "clinic", app "reception", settings configured
(Africa/Dar_es_Salaam, WhiteNoise, SQLite path, 10-minute session timeout, CLINIC_NAME),
WAL mode in reception/apps.py, models in reception/models.py:
Service, Visit, ReceiptCounter, Payment, PaymentItem, DayClose, AuditLog.

RULES (never break these):
1. Money is stored as integers (TZS). Never float or Decimal.
2. Nothing is ever deleted. Payments are voided, not removed. Use on_delete=PROTECT.
3. Amounts are always calculated on the server from the price list. The receptionist never types a price.
4. PaymentItem copies the service name and price at payment time.
5. Receipt numbers are sequential with no gaps or duplicates, generated inside transaction.atomic().
6. Two roles: Receptionist (register, take payment, print, reprint, close day) and Owner
   (everything plus reports, voids, price list, audit log). The Owner role = superuser or group "Owner".
7. Voids are Owner-only and need a reason. Reprints print "DUPLICATE".
8. Every sensitive action writes an AuditLog row (PAY, VOID, REPRINT, VISIT, DAY_CLOSE, LOGIN).
9. Timestamps are set by the server, never typed by the user.
10. The app must work with no internet.

ENVIRONMENT: Windows, PowerShell, venv at .\venv. Give me commands that work in PowerShell.

WORKING STYLE: small steps, one feature per task. After each task: run
"python manage.py check" and "python manage.py test", fix failures, then tell me
what files you changed and how to test it manually. Do not add features I did not ask for.
Do not change the rules above. Ask me before adding any new package.