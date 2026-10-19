from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver

from .models import AuditLog


@receiver(user_logged_in, dispatch_uid="reception.audit_successful_login")
def audit_successful_login(sender, request, user, **kwargs):
    AuditLog.objects.create(user=user, action="LOGIN", detail="Successful login")


@receiver(user_login_failed, dispatch_uid="reception.audit_failed_login")
def audit_failed_login(sender, credentials, request, **kwargs):
    username = str(credentials.get("username", "")).strip()
    detail = "Failed login attempt"
    if username:
        detail = f"Failed login attempt for {username}"
    AuditLog.objects.create(user=None, action="LOGIN", detail=detail)
