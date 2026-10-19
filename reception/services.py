from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from .models import AuditLog, Payment, PaymentItem, ReceiptCounter, Service


def is_owner(user):
    """Return whether a user is allowed to perform owner-only actions."""
    return bool(
        user
        and user.is_authenticated
        and (user.is_superuser or user.groups.filter(name="Owner").exists())
    )


def owner_required(view):
    @login_required
    @wraps(view)
    def wrapped_view(request, *args, **kwargs):
        if not is_owner(request.user):
            raise PermissionDenied("Owner access is required.")
        return view(request, *args, **kwargs)

    return wrapped_view


def log(user, action, detail):
    return AuditLog.objects.create(user=user, action=action, detail=detail)


def next_receipt_no():
    """Reserve and return the next receipt number."""
    with transaction.atomic():
        counter, _ = ReceiptCounter.objects.select_for_update().get_or_create(pk=1)
        counter.last_number += 1
        counter.save(update_fields=["last_number"])
        return counter.last_number


def record_payment(visit, services, user):
    """Create a payment and receipt lines from the current server-side price list."""
    selected = list(services)
    if not selected:
        raise ValidationError("At least one service is required.")

    service_ids = [service.pk for service in selected]
    if any(service_id is None for service_id in service_ids):
        raise ValidationError("Each selected service must be saved.")

    with transaction.atomic():
        current_services = Service.objects.in_bulk(service_ids)
        if len(current_services) != len(set(service_ids)):
            raise ValidationError("A selected service does not exist.")

        priced_services = [current_services[service_id] for service_id in service_ids]
        payment = Payment.objects.create(
            receipt_no=next_receipt_no(),
            visit=visit,
            total=sum(service.price for service in priced_services),
            received_by=user,
        )
        PaymentItem.objects.bulk_create(
            [
                PaymentItem(
                    payment=payment,
                    service=service,
                    name=service.name,
                    price=service.price,
                )
                for service in priced_services
            ]
        )
        log(user, "PAY", f"Receipt {payment.receipt_no}: TZS {payment.total}")
        return payment


def void_payment(payment, user, reason):
    if not is_owner(user):
        raise PermissionDenied("Only an owner can void a payment.")
    if not reason or not reason.strip():
        raise ValidationError("A void reason is required.")

    with transaction.atomic():
        payment = Payment.objects.select_for_update().get(pk=payment.pk)
        if payment.voided:
            raise ValidationError("This payment has already been voided.")
        payment.voided = True
        payment.void_reason = reason.strip()
        payment.voided_by = user
        payment.voided_at = timezone.now()
        payment.save(update_fields=["voided", "void_reason", "voided_by", "voided_at"])
        log(user, "VOID", f"Receipt {payment.receipt_no}: {payment.void_reason}")
        return payment


def register_reprint(payment, user):
    with transaction.atomic():
        stored_payment = Payment.objects.select_for_update().get(pk=payment.pk)
        stored_payment.reprints += 1
        stored_payment.save(update_fields=["reprints"])
        log(user, "REPRINT", f"Receipt {stored_payment.receipt_no}")
        payment.reprints = stored_payment.reprints
        return stored_payment
