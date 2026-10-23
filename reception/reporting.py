
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth

from .models import DayClose, Payment, PaymentItem, Visit


def report_data(start_date, end_date):
    """Return owner report data for the inclusive date range."""

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
    by_day = {row["day"]: row["revenue"] for row in daily_rows}
    day_closes = DayClose.objects.filter(date__range=(start_date, end_date)).select_related("closed_by")
    closes_by_day = {close.date: close for close in day_closes}
    each_day = []
    cursor = start_date
    while cursor <= end_date:
        revenue = by_day.get(cursor, 0)
        close = closes_by_day.get(cursor)
        each_day.append({"day": cursor, "receipts": payments.filter(paid_at__date=cursor).count(), "revenue": revenue, "close": close, "difference": close.difference if close else None, "status": "Closed" if close else "Not closed"})
        cursor += __import__("datetime").timedelta(days=1)
    period_days = (end_date - start_date).days + 1
    previous_start = start_date - __import__("datetime").timedelta(days=period_days)
    previous_end = start_date - __import__("datetime").timedelta(days=1)
    previous_revenue = Payment.objects.filter(paid_at__date__range=(previous_start, previous_end)).aggregate(total=Sum("total"))["total"] or 0
    revenue_total = payments.aggregate(total=Sum("total"))["total"] or 0
    grouping = "day"
    chart_rows = daily_rows
    if period_days > 31:
        grouping = "week"
        chart_rows = list(payments.annotate(day=TruncWeek("paid_at")).values("day").annotate(revenue=Sum("total")).order_by("day"))

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
        number
        for number in receipt_gaps
        if number not in receipt_numbers
    ]

    return {
        "start_date": start_date,
        "end_date": end_date,
        "visit_count": Visit.objects.filter(
            created_at__date__range=(start_date, end_date)
        ).count(),
        "receipt_count": payments.count(),
        "revenue_total": revenue_total,
        "reprint_count": (
            payments.aggregate(total=Sum("reprints"))["total"] or 0
        ),
        "daily_rows": daily_rows,
        "each_day": each_day,
        "chart_rows": chart_rows,
        "grouping": grouping,
        "previous_revenue": previous_revenue,
        "revenue_difference": revenue_total - previous_revenue,
        "revenue_percentage": ((revenue_total - previous_revenue) * 100 // previous_revenue) if previous_revenue else None,
        "average_per_day": revenue_total // period_days,
        "service_rows": service_rows,
        "receptionist_rows": receptionist_rows,
        "receipt_gaps": receipt_gaps,
        "day_closes": day_closes,
    }
