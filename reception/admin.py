from django.contrib import admin

from .models import DayClose, Patient, Payment, PaymentItem, Service, Visit


admin.site.register(Service)


class ReadOnlyAdmin(admin.ModelAdmin):
    """Permit inspection in admin, but never creation or alteration."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Visit, ReadOnlyAdmin)
admin.site.register(Patient, ReadOnlyAdmin)
admin.site.register(Payment, ReadOnlyAdmin)
admin.site.register(PaymentItem, ReadOnlyAdmin)
admin.site.register(DayClose, ReadOnlyAdmin)
