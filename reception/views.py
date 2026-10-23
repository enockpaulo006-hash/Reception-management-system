
from datetime import date, datetime, timedelta
from io import BytesIO
from pathlib import Path

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Count, Max, Q, Sum
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.conf import settings

from .clinic_settings import set_clinic_name
from .forms import (
    OwnPasswordChangeForm,
    ReceptionistCreationForm,
    SetupForm,
    UserPasswordResetForm,
    PatientEditForm, PatientForm, VisitAgeForm,
)
from .models import AuditLog, ClinicSettings, DayClose, Patient, Payment, Service, Visit
from .reporting import report_data
from .services import (
    is_owner,
    log,
    owner_required,
    record_payment,
    register_reprint,
)


BACKUP_TIMESTAMP_PATH = Path(
    r"C:\ProgramData\ClinicReception\backup\last_backup.txt"
)


def setup(request):
    if User.objects.exists():
        raise Http404

    if request.method == "POST":
        form = SetupForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                owner_group, _ = Group.objects.get_or_create(name="Owner")
                receptionist_group, _ = Group.objects.get_or_create(
                    name="Receptionist"
                )

                owner_name_parts = (
                    form.cleaned_data["owner_full_name"]
                    .strip()
                    .split(maxsplit=1)
                )

                owner = User.objects.create_user(
                    username=form.cleaned_data["owner_username"],
                    password=form.cleaned_data["owner_password1"],
                    first_name=owner_name_parts[0],
                    last_name=(
                        owner_name_parts[1]
                        if len(owner_name_parts) > 1
                        else ""
                    ),
                    is_staff=True,
                    is_superuser=True,
                )
                owner.groups.add(owner_group)

                receptionist_username = (
                    form.cleaned_data["receptionist_username"].strip()
                )

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

            messages.success(
                request,
                "Setup complete. Sign in with the owner account.",
            )
            return redirect("login")
    else:
        form = SetupForm()

    return render(request, "reception/setup.html", {"form": form})


def _backup_warning():
    """Warn if the recorded local backup timestamp is stale."""
    try:
        timestamp = datetime.fromisoformat(
            BACKUP_TIMESTAMP_PATH.read_text(encoding="utf-8").strip()
        )

        if timezone.is_naive(timestamp):
            timestamp = timezone.make_aware(
                timestamp,
                timezone.get_current_timezone(),
            )
    except (OSError, ValueError):
        return None

    if timezone.now() - timestamp > timedelta(hours=24):
        return "Last backup is more than 24 hours old. Check the local backup."

    return None


@login_required
def dashboard(request):
    today = timezone.localdate()

    today_visits = Visit.objects.filter(created_at__date=today).select_related("patient")
    today_payments = Payment.objects.filter(
        paid_at__date=today
    ).select_related("visit__patient")

    context = {
        "today": today,
        "visit_count": today_visits.count(),
        "receipt_count": today_payments.count(),
        "revenue_total": (
            today_payments.aggregate(total=Sum("total"))["total"] or 0
        ),
        "payments": today_payments.order_by("-paid_at"),
        "visits": today_visits.order_by("-created_at"),
        "backup_warning": _backup_warning(),
    }

    return render(request, "reception/dashboard.html", context)


@login_required
def visit_new(request):
    selected_patient = None
    if request.GET.get("patient"):
        selected_patient = get_object_or_404(Patient, pk=request.GET["patient"])
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "choose":
            return redirect(f"{redirect('visit_new').url}?patient={request.POST['patient']}")
        if action == "create_patient":
            patient_form = PatientForm(request.POST)
            if patient_form.is_valid():
                name = patient_form.full_name()
                duplicate = Patient.objects.filter(name=name, phone=patient_form.cleaned_data["phone"]).first()
                if duplicate:
                    messages.warning(request, "A patient with this name and phone already exists. Use the existing patient instead.")
                    return render(request, "reception/visit_form.html", {"patient_form": patient_form, "duplicate": duplicate})
                patient = Patient.objects.create(name=name, first_name=patient_form.cleaned_data["first_name"], second_name=patient_form.cleaned_data["second_name"], phone=patient_form.cleaned_data["phone"], sex=patient_form.cleaned_data["sex"], created_by=request.user)
                return redirect(f"{redirect('visit_new').url}?patient={patient.pk}")
        elif action == "age" and selected_patient:
            age_form = VisitAgeForm(request.POST)
            if age_form.is_valid():
                visit = Visit.objects.create(patient=selected_patient, name=selected_patient.name, phone=selected_patient.phone, sex=selected_patient.sex, age=age_form.cleaned_data["age"], created_by=request.user)
                log(request.user, "VISIT", f"Visit {visit.pk} registered")
                return redirect("visit_pay", pk=visit.pk)
        else:
            age_form = VisitAgeForm()
    query = request.GET.get("q", "").strip()
    patients = Patient.objects.filter(Q(name__icontains=query) | Q(phone__icontains=query)).order_by("name") if query else Patient.objects.none()
    return render(request, "reception/visit_form.html", {"patients": patients, "query": query, "selected_patient": selected_patient, "patient_form": locals().get("patient_form", PatientForm()), "age_form": locals().get("age_form", VisitAgeForm())})


@login_required
def patient_list(request):
    query = request.GET.get("q", "").strip()
    patients = Patient.objects.annotate(last_visit=Max("visits__created_at"), visit_count=Count("visits"), total_paid=Sum("visits__payments__total"))
    if query:
        patients = patients.filter(Q(name__icontains=query) | Q(phone__icontains=query))
    page = Paginator(patients.order_by("name"), 25).get_page(request.GET.get("page"))
    return render(request, "reception/patient_list.html", {"page_obj": page, "query": query})


@login_required
def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == "POST":
        form = PatientEditForm(request.POST)
        if form.is_valid():
            patient.first_name = form.cleaned_data["first_name"]
            patient.second_name = form.cleaned_data["second_name"]
            patient.name = f"{patient.first_name.strip()} {patient.second_name.strip()}".strip()
            patient.phone = form.cleaned_data["phone"]
            patient.save(update_fields=["first_name", "second_name", "name", "phone"])
            return redirect("patient_detail", pk=pk)
    else:
        form = PatientEditForm(initial={"first_name": patient.first_name or patient.name.split(" ", 1)[0], "second_name": patient.second_name or (patient.name.split(" ", 1)[1] if " " in patient.name else ""), "phone": patient.phone})
    visits = patient.visits.select_related("created_by").prefetch_related("payments__items").order_by("-created_at")
    payments = Payment.objects.filter(visit__patient=patient).select_related("received_by").prefetch_related("items").order_by("-paid_at")
    return render(request, "reception/patient_detail.html", {"patient": patient, "visits": visits, "payments": payments, "form": form, "total_paid": sum(payment.total for payment in payments)})


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

    return render(
        request,
        "reception/password_form.html",
        {"form": form, "heading": "My password"},
    )


@owner_required
def user_list(request):
    users = list(
        User.objects.prefetch_related("groups").order_by("username")
    )

    for listed_user in users:
        listed_user.role = (
            "Owner" if is_owner(listed_user) else "Receptionist"
        )

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

            receptionist_group, _ = Group.objects.get_or_create(
                name="Receptionist"
            )
            user.groups.add(receptionist_group)

            log(request.user, "USER_CREATE", f"Created receptionist {user.username}")
            messages.success(
                request,
                f"Receptionist {user.username} was created.",
            )

            return redirect("user_list")
    else:
        form = ReceptionistCreationForm()

    return render(
        request,
        "reception/user_form.html",
        {
            "form": form,
            "heading": "New receptionist",
            "submit_label": "Create receptionist",
        },
    )


@owner_required
def user_password_reset(request, pk):
    target_user = get_object_or_404(User, pk=pk)

    if request.method == "POST":
        form = UserPasswordResetForm(target_user, request.POST)

        if form.is_valid():
            form.save()

            log(
                request.user,
                "PASSWORD_RESET",
                f"Reset password for {target_user.username}",
            )
            messages.success(
                request,
                f"Password reset for {target_user.username}.",
            )

            return redirect("user_list")
    else:
        form = UserPasswordResetForm(target_user)

    return render(
        request,
        "reception/password_form.html",
        {
            "form": form,
            "heading": f"Reset password: {target_user.username}",
            "submit_label": "Set new password",
        },
    )


def _active_owner_count():
    return (
        User.objects.filter(is_active=True)
        .filter(Q(is_superuser=True) | Q(groups__name="Owner"))
        .distinct()
        .count()
    )


@owner_required
@require_POST
def user_toggle(request, pk):
    target_user = get_object_or_404(User, pk=pk)

    if (
        target_user.is_active
        and is_owner(target_user)
        and _active_owner_count() <= 1
    ):
        messages.error(
            request,
            "You cannot deactivate the last active owner.",
        )
    elif target_user == request.user:
        messages.error(
            request,
            "You cannot deactivate your own account.",
        )
    else:
        target_user.is_active = not target_user.is_active
        target_user.save(update_fields=["is_active"])

        action = (
            "USER_ACTIVATE"
            if target_user.is_active
            else "USER_DEACTIVATE"
        )

        log(
            request.user,
            action,
            f"{action.replace('_', ' ').title()}: {target_user.username}",
        )

        messages.success(
            request,
            f"{target_user.username} is now "
            f"{'active' if target_user.is_active else 'inactive'}.",
        )

    return redirect("user_list")


@login_required
def visit_pay(request, pk):
    visit = get_object_or_404(Visit, pk=pk)

    active_services = Service.objects.filter(active=True)
    consultations = active_services.filter(
        kind="CONSULT"
    ).order_by("name")
    tests = active_services.filter(
        kind="TEST"
    ).order_by("name")

    if request.method == "POST":
        selected_ids = request.POST.getlist("services")

        if not selected_ids:
            messages.error(
                request,
                "Please select at least one service.",
            )

        elif len(selected_ids) != len(set(selected_ids)):
            messages.error(
                request,
                "Duplicate service selections are not allowed.",
            )

        else:
            selected_services = active_services.filter(
                pk__in=selected_ids
            )

            if selected_services.count() != len(selected_ids):
                messages.error(
                    request,
                    "One or more selected services are unavailable.",
                )
            else:
                selected_kinds = set(
                    selected_services.values_list("kind", flat=True)
                )

                if len(selected_kinds) > 1:
                    messages.error(
                        request,
                        "Select consultation services or laboratory tests "
                        "for a receipt, not both.",
                    )
                else:
                    try:
                        payment = record_payment(
                            visit,
                            selected_services,
                            request.user,
                        )
                    except ValidationError as error:
                        messages.error(
                            request,
                            "; ".join(error.messages),
                        )
                    else:
                        receipt_url = redirect(
                            "receipt_detail",
                            no=payment.receipt_no,
                        ).url

                        return HttpResponseRedirect(
                            f"{receipt_url}?print=1"
                        )

    today = timezone.localdate()

    consultation_paid_today = Payment.objects.filter(
        visit=visit,
        paid_at__date=today,
        items__service__kind="CONSULT",
    ).exists()

    context = {
        "visit": visit,
        "consultations": consultations,
        "tests": tests,
        "consultation_paid_today": consultation_paid_today,
        "consultation_enabled": not consultation_paid_today,
        "tests_enabled": consultation_paid_today,
        "earlier_receipts": (
            visit.payments
            .select_related("received_by")
            .order_by("-paid_at")
        ),
    }

    return render(
        request,
        "reception/visit_pay.html",
        context,
    )


@login_required
def receipt_detail(request, no):
    payment = get_object_or_404(
        Payment.objects.select_related(
            "visit__patient",
            "received_by",
        ).prefetch_related("items"),
        receipt_no=no,
    )

    return render(
        request,
        "reception/receipt_detail.html",
        {"payment": payment},
    )


@login_required
@require_POST
def receipt_reprint(request, no):
    payment = get_object_or_404(Payment, receipt_no=no)
    register_reprint(payment, request.user)

    receipt_url = redirect("receipt_detail", no=no).url

    return HttpResponseRedirect(
        f"{receipt_url}?copy=1&print=1"
    )


@login_required
def day_close(request):
    today = timezone.localdate()

    payments = Payment.objects.filter(paid_at__date=today)
    expected_cash = (
        payments.aggregate(total=Sum("total"))["total"] or 0
    )
    receipt_count = payments.count()
    day_close = DayClose.objects.filter(date=today).first()

    if request.method == "POST":
        counted_value = request.POST.get("counted_cash", "").strip()
        note = request.POST.get("note", "").strip()

        try:
            counted_cash = int(counted_value)

            if counted_cash < 0:
                raise ValueError
        except ValueError:
            messages.error(
                request,
                "Counted cash must be a whole number of TZS or greater.",
            )
        else:
            if len(note) > 255:
                messages.error(
                    request,
                    "The note must be 255 characters or fewer.",
                )
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
                            f"{today}: expected TZS {expected_cash}, "
                            f"counted TZS {counted_cash}",
                        )

                if created:
                    return redirect("day_close")

                messages.error(
                    request,
                    "Today has already been closed. "
                    "A second close is not allowed.",
                )

    context = {
        "today": today,
        "receipt_count": receipt_count,
        "day_close": day_close,
        "is_owner": is_owner(request.user),
    }

    # Do not expose expected cash to receptionists before day closing.
    if day_close is None and is_owner(request.user):
        context["expected_cash"] = expected_cash

    return render(
        request,
        "reception/day_close.html",
        context,
    )


def _report_dates(request):
    today = timezone.localdate()

    try:
        start_date = date.fromisoformat(
            request.GET.get("start", today.isoformat())
        )
        end_date = date.fromisoformat(
            request.GET.get("end", today.isoformat())
        )
    except ValueError:
        messages.error(
            request,
            "Use valid dates in YYYY-MM-DD format.",
        )
        return today, today

    if start_date > end_date:
        messages.error(
            request,
            "The start date cannot be after the end date.",
        )
        return today, today

    return start_date, end_date


@owner_required
def reports(request):
    today = timezone.localdate()
    settings_row, _ = ClinicSettings.objects.get_or_create(pk=1)
    if settings_row.last_report_open != today:
        settings_row.previous_report_open = settings_row.last_report_open
        settings_row.last_report_open = today
        settings_row.save(update_fields=["previous_report_open", "last_report_open"])
    if request.GET.get("period") == "month":
        start_date, end_date = today.replace(day=1), today
    elif request.GET.get("period") == "last_month":
        end_date = today.replace(day=1) - timedelta(days=1); start_date = end_date.replace(day=1)
    elif "start" in request.GET or "end" in request.GET:
        start_date, end_date = _report_dates(request)
    else:
        start_date = settings_row.previous_report_open or (today - timedelta(days=6)); end_date = today
    data = report_data(start_date, end_date)
    data["since_last_visit"] = settings_row.previous_report_open
    return render(request, "reception/reports.html", data)


@owner_required
def report_day(request, report_date):
    selected = get_object_or_404(DayClose, date=report_date) if False else date.fromisoformat(report_date)
    payments = Payment.objects.filter(paid_at__date=selected).select_related("visit__patient", "received_by").prefetch_related("items")
    return render(request, "reception/report_day.html", {"day": selected, "payments": payments})


def _add_sheet(workbook, title, headers, rows):
    from openpyxl.styles import Font
    sheet = workbook.create_sheet(title)
    sheet.append(headers)

    for cell in sheet[1]:
        cell.font = Font(bold=True)

    for row in rows:
        sheet.append(row)

    sheet.freeze_panes = "A2"

    for column in sheet.columns:
        sheet.column_dimensions[
            column[0].column_letter
        ].width = min(
            max(len(str(cell.value or "")) for cell in column) + 2,
            32,
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
            ("Revenue (TZS)", data["revenue_total"]),
            ("Reprints", data["reprint_count"]),
        ],
    )

    _add_sheet(
        workbook,
        "Revenue by day",
        ["Date", "Revenue (TZS)"],
        [
            (row["day"], row["revenue"])
            for row in data["daily_rows"]
        ],
    )

    _add_sheet(
        workbook,
        "Services",
        ["Service", "Count", "Revenue (TZS)"],
        [
            (row["name"], row["count"], row["revenue"])
            for row in data["service_rows"]
        ],
    )

    _add_sheet(
        workbook,
        "Receptionists",
        ["Receptionist", "Receipts", "Revenue (TZS)"],
        [
            (
                row["received_by__username"],
                row["count"],
                row["revenue"],
            )
            for row in data["receptionist_rows"]
        ],
    )

    _add_sheet(
        workbook,
        "Receipt gaps",
        ["Missing receipt number"],
        [(number,) for number in data["receipt_gaps"]],
    )

    _add_sheet(
        workbook,
        "Day closes",
        [
            "Date",
            "Expected (TZS)",
            "Counted (TZS)",
            "Difference (TZS)",
            "Closed by",
        ],
        [
            (
                close.date,
                close.expected_cash,
                close.counted_cash,
                close.difference,
                close.closed_by.get_username(),
            )
            for close in data["day_closes"]
        ],
    )

    output = BytesIO()
    workbook.save(output)

    response = HttpResponse(
        output.getvalue(),
        content_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
    )

    response["Content-Disposition"] = (
        'attachment; filename="clinic-report.xlsx"'
    )

    return response


def audit_log(request):
    if not settings.SHOW_AUDIT_LOG:
        raise Http404
    if not is_owner(request.user):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Owner access is required.")
    selected_date = request.GET.get("date", "")
    selected_action = request.GET.get("action", "")

    logs = AuditLog.objects.select_related("user").all()

    if selected_date:
        try:
            logs = logs.filter(
                at__date=date.fromisoformat(selected_date)
            )
        except ValueError:
            messages.error(
                request,
                "Use a valid date in YYYY-MM-DD format.",
            )
            selected_date = ""

    if selected_action:
        logs = logs.filter(action=selected_action)

    return render(
        request,
        "reception/audit_log.html",
        {
            "logs": logs,
            "actions": (
                AuditLog.objects.order_by("action")
                .values_list("action", flat=True)
                .distinct()
            ),
            "selected_date": selected_date,
            "selected_action": selected_action,
        },
    )
