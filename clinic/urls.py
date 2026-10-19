"""
URL configuration for clinic project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.urls import path

from reception import views
from reception.forms import ClinicAuthenticationForm

urlpatterns = [
    path('setup/', views.setup, name='setup'),
    path('admin/', admin.site.urls),
    path('', views.dashboard, name='dashboard'),
    path('login/', auth_views.LoginView.as_view(authentication_form=ClinicAuthenticationForm), name='login'),
    path('logout/', login_required(auth_views.LogoutView.as_view()), name='logout'),
    path('visit/new/', views.visit_new, name='visit_new'),
    path('account/password/', views.account_password, name='account_password'),
    path('users/', views.user_list, name='user_list'),
    path('users/new/', views.user_new, name='user_new'),
    path('users/<int:pk>/password/', views.user_password_reset, name='user_password_reset'),
    path('users/<int:pk>/toggle/', views.user_toggle, name='user_toggle'),
    path('visit/<int:pk>/pay/', views.visit_pay, name='visit_pay'),
    path('receipt/<int:no>/', views.receipt_detail, name='receipt_detail'),
    path('receipt/<int:no>/reprint/', views.receipt_reprint, name='receipt_reprint'),
    path('receipt/<int:no>/void/', views.receipt_void, name='receipt_void'),
    path('day/close/', views.day_close, name='day_close'),
    path('reports/', views.reports, name='reports'),
    path('reports/export/', views.reports_export, name='reports_export'),
    path('audit/', views.audit_log, name='audit_log'),
]
