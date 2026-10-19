from datetime import date, datetime, timedelta
from io import BytesIO
from pathlib import Path

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q, Sum
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from openpyxl.styles import Font

from .clinic_settings import set_clinic_name
from .forms import OwnPasswordChangeForm, ReceptionistCreationForm, SetupForm, UserPasswordResetForm, VisitForm
from .models import AuditLog, DayClose, Payment, Service, Visit
from .reporting import report_data
from .services import is_owner, log, owner_required, record_payment, register_reprint, void_payment


BACKUP_TIMESTAMP_PATH = Path(r"C:\ProgramData\ClinicReception\backup\last_backup.txt")


def setup(request):
    if User.objects.exists():
        raise Http404
    if request.method == "POST":
        form = SetupForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                owner_group, _ = Group.objects.get_or_create(name="Owner")
                receptionist_group, _ = Group.objects.get_or_create(name="Receptionist")
                owner_name_parts = form.cleaned_data["owner_full_name"].strip().split(maxsplit=1)
                owner = User.objects.create_user(
                    username=form.cleaned_data["owner_username"],
                    password=form.cleaned_data["owner_password1"],
                    first_name=owner_name_parts[0],
                    last_name=owner_name_parts[1] if len(owner_name_parts) > 1 else "",
                    is_staff=True,
                    is_superuser=True,
                )
                owner.groups.add(owner_group)
                receptionist_username = form.cleaned_data["receptionist_username"].strip()
                if receptionist_username:
                    receptionist = User.objects.create_user(
                        username=receptionist_username,
                        password=form.cleaned_data["receptionist_password"],
                        is_staff=False,
                        is_superuser=False,
                    )
                    receptionist.groups.add(receptionist_group)
                set_clinic_name(form.cleaned_data["clinic_name"])
                log(owner, "SETUP", "Initial clinic setup completed")
            messages.success(request, "Setup complete. Sign in with the owner account.")
            return redirect("login")
    else:
        form = SetupForm()
    return render(request, "reception/setup.html", {"form": form})


def _backup_warning():
    """Return a warning only when a readable local backup timestamp is stale."""
    try:
        timestamp = datetime.fromisoformat(BACKUP_TIMESTAMP_PATH.read_text(encoding="utf-8").strip())
        if timezone.is_naive(timestamp):
            timestamp = timezone.make_aware(timestamp, timezone.get_current_timezone())
    except (OSError, ValueError):
        return None
    if timezone.now() - timestamp > timedelta(hours=24):
        return "Last backup is more than 24 hours old. Check the local backup."
    return None


@login_required
def dashboard(request):
    today = timezone.localdate()
    today_visits = Visit.objects.filter(created_at__date=today)
    today_payments = Payment.objects.filter(paid_at__date=today).select_related("visit")
    valid_payments = today_payments.filter(voided=False)

    context = {
        "today": today,
        "visit_count": today_visits.count(),
        "receipt_count": today_payments.count(),
        "revenue_total": valid_payments.aggregate(total=Sum("total"))["total"] or 0,
        "voided_count": today_payments.filter(voided=True).count(),
        "payments": today_payments.order_by("-paid_at"),
        "visits": today_visits.order_by("-created_at"),
        "backup_warning": _backup_warning(),
    }
    return render(request, "reception/dashboard.html", context)


@login_required
def visit_new(request):
    if request.method == "POST":
        form = VisitForm(request.POST)
        if form.is_valid():
            visit = form.save(commit=False)
            visit.created_by = request.user
            visit.save()
            log(request.user, "VISIT", f"Visit {visit.pk} registered")
            return redirect("visit_pay", pk=visit.pk)
    else:
        form = VisitForm()
    return render(request, "reception/visit_form.html", {"form": form})


@login_required
def account_password(request):
    if request.method == "POST":
        form = OwnPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            log(request.user, "PASSWORD_CHANGE", "Changed own password")
            messages.success(request, "Your password has been changed.")
            return redirect("dashboard")
    else:
        form = OwnPasswordChangeForm(request.user)
    return render(request, "reception/password_form.html", {"form": form, "heading": "My password"})


@owner_required
def user_list(request):
    users = list(User.objects.prefetch_related("groups").order_by("username"))
    for listed_user in users:
        listed_user.role = "Owner" if is_owner(listed_user) else "Receptionist"
    return render(request, "reception/user_list.html", {"users": users})


@owner_required
def user_new(request):
    if request.method == "POST":
        form = ReceptionistCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True
            user.is_staff = False
            user.is_superuser = False
            user.save()
            receptionist_group, _ = Group.objects.get_or_create(name="Receptionist")
            user.groups.add(receptionist_group)
            log(request.user, "USER_CREATE", f"Created receptionist {user.username}")
            messages.success(request, f"Receptionist {user.username} was created.")
            return redirect("user_list")
    else:
        form = ReceptionistCreationForm()
    return render(request, "reception/user_form.html", {"form": form, "heading": "New receptionist", "submit_label": "Create receptionist"})


@owner_required
def user_password_reset(request, pk):
    target_user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = UserPasswordResetForm(target_user, request.POST)
        if form.is_valid():
            form.save()
            log(request.user, "PASSWORD_RESET", f"Reset password for {target_user.username}")
            messages.success(request, f"Password reset for {target_user.username}.")
            return redirect("user_list")
    else:
        form = UserPasswordResetForm(target_user)
    return render(request, "reception/password_form.html", {"form": form, "heading": f"Reset password: {target_user.username}", "submit_label": "Set new password"})


def _active_owner_count():
    return User.objects.filter(is_active=True).filter(
        Q(is_superuser=True) | Q(groups__name="Owner")
    ).distinct().count()


@owner_required
@require_POST
def user_toggle(request, pk):
    target_user = get_object_or_404(User, pk=pk)
    if target_user.is_active and is_owner(target_user) and _active_owner_count() <= 1:
        messages.error(request, "You cannot deactivate the last active owner.")
    elif target_user == request.user:
        messages.error(request, "You cannot deactivate your own account.")
    else:
        target_user.is_active = not target_user.is_active
        target_user.save(update_fields=["is_active"])
        action = "USER_ACTIVATE" if target_user.is_active else "USER_DEACTIVATE"
        log(request.user, action, f"{action.replace('_', ' ').title()}: {target_user.username}")
        messages.success(request, f"{target_user.username} is now {'active' if target_user.is_active else 'inactive'}.")
    return redirect("user_list")


@login_required
def visit_pay(request, pk):
    visit = get_object_or_404(Visit, pk=pk)
    active_services = Service.objects.filter(active=True)
    if request.method == "POST":
        selected_ids = request.POST.getlist("services")
        selected_services = Service.objects.filter(pk__in=selected_ids, active=True)
        if not selected_ids:
            messages.error(request, "Select at least one service.")
        elif len(selected_ids) != len(set(selected_ids)) or selected_services.count() != len(selected_ids):
            messages.error(request, "One or more selected services are unavailable.")
        else:
            try:
                payment = record_payment(visit, selected_services, request.user)
            except ValidationError as error:
                messages.error(request, "; ".join(error.messages))
            else:
                return HttpResponseRedirect(
                    f"{redirect('receipt_detail', no=payment.receipt_no).url}?print=1"
                )

    return render(
        request,
        "reception/visit_pay.html",
        {
            "visit": visit,
            "consultations": active_services.filter(kind="CONSULT"),
            "tests": active_services.filter(kind="TEST"),
            "earlier_receipts": visit.payments.select_related("received_by").order_by("-paid_at"),
        },
    )


@login_required
def receipt_detail(request, no):
    payment = get_object_or_404(
        Payment.objects.select_related("visit", "received_by", "voided_by").prefetch_related("items"),
        receipt_no=no,
    )
    return render(
        request,
        "reception/receipt_detail.html",
        {"payment": payment, "can_void": is_owner(request.user)},
    )


@login_required
@require_POST
def receipt_reprint(request, no):
    payment = get_object_or_404(Payment, receipt_no=no)
    register_reprint(payment, request.user)
    return HttpResponseRedirect(f"{redirect('receipt_detail', no=no).url}?copy=1&print=1")


@login_required
@require_POST
def receipt_void(request, no):
    payment = get_object_or_404(Payment, receipt_no=no)
    try:
        void_payment(payment, request.user, request.POST.get("reason", ""))
    except PermissionDenied:
        messages.error(request, "Only the owner can void a receipt")
    except ValidationError as error:
        messages.error(request, "; ".join(error.messages))
    else:
        messages.success(request, f"Receipt {payment.receipt_no} was voided.")
    return redirect("receipt_detail", no=no)


@login_required
def day_close(request):
    today = timezone.localdate()
    payments = Payment.objects.filter(paid_at__date=today)
    expected_cash = payments.filter(voided=False).aggregate(total=Sum("total"))["total"] or 0
    receipt_count = payments.count()
    voided_count = payments.filter(voided=True).count()
    day_close = DayClose.objects.filter(date=today).first()

    if request.method == "POST":
        counted_value = request.POST.get("counted_cash", "").strip()
        note = request.POST.get("note", "").strip()
        try:
            counted_cash = int(counted_value)
            if counted_cash < 0:
                raise ValueError
        except ValueError:
            messages.error(request, "Counted cash must be a whole number of TZS or greater.")
        else:
            if len(note) > 255:
                messages.error(request, "The note must be 255 characters or fewer.")
            else:
                with transaction.atomic():
                    day_close, created = DayClose.objects.get_or_create(
                        date=today,
                        defaults={
                            "expected_cash": expected_cash,
                            "counted_cash": counted_cash,
                            "difference": counted_cash - expected_cash,
                            "closed_by": request.user,
                            "note": note,
                        },
                    )
                    if created:
                        log(
                            request.user,
                            "DAY_CLOSE",
                            f"{today}: expected TZS {expected_cash}, counted TZS {counted_cash}",
                        )
                if created:
                    return redirect("day_close")
                messages.error(request, "Today has already been closed. A second close is not allowed.")

    context = {
        "today": today,
        "receipt_count": receipt_count,
        "voided_count": voided_count,
        "day_close": day_close,
        "is_owner": is_owner(request.user),
    }
    # Never place the expected cash in a receptionist's pre-close response.
    if day_close is None and is_owner(request.user):
        context["expected_cash"] = expected_cash
    return render(request, "reception/day_close.html", context)


def _report_dates(request):
    today = timezone.localdate()
    try:
        start_date = date.fromisoformat(request.GET.get("start", today.isoformat()))
        end_date = date.fromisoformat(request.GET.get("end", today.isoformat()))
    except ValueError:
        messages.error(request, "Use valid dates in YYYY-MM-DD format.")
        return today, today
    if start_date > end_date:
        messages.error(request, "The start date cannot be after the end date.")
        return today, today
    return start_date, end_date


@owner_required
def reports(request):
    start_date, end_date = _report_dates(request)
    return render(request, "reception/reports.html", report_data(start_date, end_date))


def _add_sheet(workbook, title, headers, rows):
    sheet = workbook.create_sheet(title)
    sheet.append(headers)
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    for row in rows:
        sheet.append(row)
    sheet.freeze_panes = "A2"
    for column in sheet.columns:
        sheet.column_dimensions[column[0].column_letter].width = min(
            max(len(str(cell.value or "")) for cell in column) + 2, 32
        )


@owner_required
def reports_export(request):
    from openpyxl import Workbook

    data = report_data(*_report_dates(request))
    workbook = Workbook()
    workbook.remove(workbook.active)
    _add_sheet(
        workbook,
        "Summary",
        ["Metric", "Value"],
        [
            ("Start date", data["start_date"]),
            ("End date", data["end_date"]),
            ("Visits", data["visit_count"]),
            ("Receipts", data["receipt_count"]),
            ("Revenue (non-voided TZS)", data["revenue_total"]),
            ("Voids", data["voided_count"]),
            ("Voided amount (TZS)", data["voided_amount"]),
            ("Reprints", data["reprint_count"]),
        ],
    )
    _add_sheet(workbook, "Revenue by day", ["Date", "Revenue (TZS)"], [(row["day"], row["revenue"]) for row in data["daily_rows"]])
    _add_sheet(workbook, "Services", ["Service", "Count", "Revenue (TZS)"], [(row["name"], row["count"], row["revenue"]) for row in data["service_rows"]])
    _add_sheet(workbook, "Receptionists", ["Receptionist", "Receipts", "Revenue (TZS)"], [(row["received_by__username"], row["count"], row["revenue"]) for row in data["receptionist_rows"]])
    _add_sheet(workbook, "Receipt gaps", ["Missing receipt number"], [(number,) for number in data["receipt_gaps"]])
    _add_sheet(
        workbook,
        "Day closes",
        ["Date", "Expected (TZS)", "Counted (TZS)", "Difference (TZS)", "Closed by"],
        [
            (close.date, close.expected_cash, close.counted_cash, close.difference, close.closed_by.get_username())
            for close in data["day_closes"]
        ],
    )

    output = BytesIO()
    workbook.save(output)
    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="clinic-report.xlsx"'
    return response


@owner_required
def audit_log(request):
    selected_date = request.GET.get("date", "")
    selected_action = request.GET.get("action", "")
    logs = AuditLog.objects.select_related("user").all()
    if selected_date:
        try:
            logs = logs.filter(at__date=date.fromisoformat(selected_date))
        except ValueError:
            messages.error(request, "Use a valid date in YYYY-MM-DD format.")
            selected_date = ""
    if selected_action:
        logs = logs.filter(action=selected_action)
    return render(
        request,
        "reception/audit_log.html",
        {
            "logs": logs,
            "actions": AuditLog.objects.order_by("action").values_list("action", flat=True).distinct(),
            "selected_date": selected_date,
            "selected_action": selected_action,
        },
    )
