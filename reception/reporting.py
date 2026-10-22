
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate

from .models import DayClose, Payment, PaymentItem, Visit


def report_data(start_date, end_date):
    """Return all owner report sections for the inclusive local-date range."""
    payments = Payment.objects.filter(
        paid_at__date__range=(start_date, end_date)
    )

    service_rows = list(
        PaymentItem.objects.filter(
            payment__paid_at__date__range=(start_date, end_date)
        )
        .values("name")
        .annotate(
            count=Count("id"),
            revenue=Sum("price"),
        )
        .order_by("name")
    )

    receptionist_rows = list(
        payments.values("received_by__username")
        .annotate(
            count=Count("id"),
            revenue=Sum("total"),
        )
        .order_by("received_by__username")
    )

    daily_rows = list(
        payments.annotate(day=TruncDate("paid_at"))
        .values("day")
        .annotate(revenue=Sum("total"))
        .order_by("day")
    )

    highest_receipt = (
        Payment.objects.order_by("-receipt_no")
        .values_list("receipt_no", flat=True)
        .first()
    )

    receipt_numbers = set(
        Payment.objects.values_list("receipt_no", flat=True)
    )

    receipt_gaps = (
        list(range(1, highest_receipt + 1))
        if highest_receipt
        else []
    )
    receipt_gaps = [
        number for number in receipt_gaps
        if number not in receipt_numbers
    ]

    return {
        "start_date": start_date,
        "end_date": end_date,
        "visit_count": Visit.objects.filter(
            created_at__date__range=(start_date, end_date)
        ).count(),
        "receipt_count": payments.count(),
        "revenue_total": payments.aggregate(
            total=Sum("total")
        )["total"] or 0,
        "reprint_count": payments.aggregate(
            total=Sum("reprints")
        )["total"] or 0,
        "daily_rows": daily_rows,
        "service_rows": service_rows,
        "receptionist_rows": receptionist_rows,
        "receipt_gaps": receipt_gaps,
        "day_closes": DayClose.objects.filter(
            date__range=(start_date, end_date)
        ).select_related("closed_by"),
    }
