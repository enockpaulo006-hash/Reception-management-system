
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
        and (
            user.is_superuser
            or user.groups.filter(name="Owner").exists()
        )
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
    return AuditLog.objects.create(
        user=user,
        action=action,
        detail=detail,
    )


def next_receipt_no():
    """Reserve and return the next receipt number."""
    with transaction.atomic():
        counter, _ = ReceiptCounter.objects.select_for_update().get_or_create(
            pk=1
        )
        counter.last_number += 1
        counter.save(update_fields=["last_number"])
        return counter.last_number


def record_payment(visit, services, user):
    """
    Record a payment while enforcing the daily payment sequence.

    Rules:
    - Consultation must be paid before laboratory tests.
    - Consultation can only be paid once per visit per local day.
    - Laboratory tests can be paid multiple times after consultation.
    - Consultation and laboratory tests must use separate receipts.
    """
    selected = list(services)

    if not selected:
        raise ValidationError("Select at least one service.")

    service_ids = [service.pk for service in selected]

    if any(service_id is None for service_id in service_ids):
        raise ValidationError("Each selected service must be saved.")

    if len(service_ids) != len(set(service_ids)):
        raise ValidationError("A service cannot be selected more than once.")

    with transaction.atomic():
        current_services = Service.objects.filter(
            pk__in=service_ids,
            active=True,
        )

        service_map = {
            service.pk: service
            for service in current_services
        }

        if len(service_map) != len(service_ids):
            raise ValidationError(
                "One or more selected services are unavailable."
            )

        priced_services = [
            service_map[service_id]
            for service_id in service_ids
        ]

        kinds = {service.kind for service in priced_services}

        if not kinds.issubset({"CONSULT", "TEST"}):
            raise ValidationError("An invalid service type was selected.")

        if len(kinds) > 1:
            raise ValidationError(
                "Pay consultation and laboratory tests on separate receipts."
            )

        today = timezone.localdate()

        consultation_paid_today = PaymentItem.objects.filter(
            payment__visit=visit,
            payment__paid_at__date=today,
            service__kind="CONSULT",
        ).exists()

        selected_kind = next(iter(kinds))

        if selected_kind == "TEST" and not consultation_paid_today:
            raise ValidationError(
                "Consultation must be paid before laboratory tests."
            )

        if selected_kind == "CONSULT" and consultation_paid_today:
            raise ValidationError(
                "Consultation has already been paid for this visit today."
            )

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

        log(
            user,
            "PAY",
            f"Receipt {payment.receipt_no}: TZS {payment.total}",
        )

        return payment


def register_reprint(payment, user):
    """Record a receipt reprint without changing the original payment."""
    with transaction.atomic():
        stored_payment = Payment.objects.select_for_update().get(
            pk=payment.pk
        )

        stored_payment.reprints += 1
        stored_payment.save(update_fields=["reprints"])

        log(
            user,
            "REPRINT",
            f"Receipt {stored_payment.receipt_no}",
        )

        payment.reprints = stored_payment.reprints

        return stored_payment
