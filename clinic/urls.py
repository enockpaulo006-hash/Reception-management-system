
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.urls import path

from reception import views
from reception.forms import ClinicAuthenticationForm


urlpatterns = [
    path("setup/", views.setup, name="setup"),
    path("admin/", admin.site.urls),
    path("", views.dashboard, name="dashboard"),

    path(
        "login/",
        auth_views.LoginView.as_view(
            authentication_form=ClinicAuthenticationForm
        ),
        name="login",
    ),
    path(
        "logout/",
        login_required(auth_views.LogoutView.as_view()),
        name="logout",
    ),

    path("visit/new/", views.visit_new, name="visit_new"),
    path("patients/", views.patient_list, name="patient_list"),
    path("patients/<int:pk>/", views.patient_detail, name="patient_detail"),
    path("visit/<int:pk>/pay/", views.visit_pay, name="visit_pay"),

    path(
        "account/password/",
        views.account_password,
        name="account_password",
    ),

    path("users/", views.user_list, name="user_list"),
    path("users/new/", views.user_new, name="user_new"),
    path(
        "users/<int:pk>/password/",
        views.user_password_reset,
        name="user_password_reset",
    ),
    path(
        "users/<int:pk>/toggle/",
        views.user_toggle,
        name="user_toggle",
    ),

    path(
        "receipt/<int:no>/",
        views.receipt_detail,
        name="receipt_detail",
    ),
    path(
        "receipt/<int:no>/reprint/",
        views.receipt_reprint,
        name="receipt_reprint",
    ),

    path("day/close/", views.day_close, name="day_close"),

    path("reports/", views.reports, name="reports"),
    path("reports/day/<str:report_date>/", views.report_day, name="report_day"),
    path(
        "reports/export/",
        views.reports_export,
        name="reports_export",
    ),
    path("audit/", views.audit_log, name="audit_log"),

]
