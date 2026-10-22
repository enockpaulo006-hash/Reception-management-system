from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db import models


class Service(models.Model):
    KINDS = [('CONSULT', 'Consultation'), ('TEST', 'Test')]
    name = models.CharField(max_length=100)
    kind = models.CharField(max_length=10, choices=KINDS)
    price = models.PositiveIntegerField(help_text='TZS')
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['kind', 'name']

    def __str__(self):
        return f'{self.name} ({self.price:,})'


class Setting(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.CharField(max_length=255)


class Visit(models.Model):
    SEX = [('M', 'Male'), ('F', 'Female')]

    name = models.CharField(max_length=120)
    first_name = models.CharField(max_length=60, blank=True, default='')
    second_name = models.CharField(max_length=60, blank=True, default='')
    phone = models.CharField(max_length=20, blank=True)
    age = models.PositiveSmallIntegerField()
    sex = models.CharField(max_length=1, choices=SEX)
    physical_address = models.CharField(max_length=255, blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='+')

    def delete(self, *a, **k):
        raise PermissionDenied('Visits cannot be deleted.')


class ReceiptCounter(models.Model):
    last_number = models.PositiveIntegerField(default=0)


class Payment(models.Model):
    receipt_no = models.PositiveIntegerField(unique=True)
    visit = models.ForeignKey(Visit, on_delete=models.PROTECT, related_name='payments')
    total = models.PositiveIntegerField()
    paid_at = models.DateTimeField(auto_now_add=True)
    received_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='+')
    reprints = models.PositiveSmallIntegerField(default=0)
    voided = models.BooleanField(default=False)
    void_reason = models.CharField(max_length=255, blank=True)
    voided_by = models.ForeignKey(User, null=True, blank=True,
                                  on_delete=models.PROTECT, related_name='+')
    voided_at = models.DateTimeField(null=True, blank=True)

    def delete(self, *a, **k):
        raise PermissionDenied('Payments cannot be deleted. Void them instead.')

    def save(self, *a, **k):
        if self.pk:
            old = Payment.objects.get(pk=self.pk)
            if (old.total, old.receipt_no, old.visit_id, old.received_by_id) != \
               (self.total, self.receipt_no, self.visit_id, self.received_by_id):
                raise PermissionDenied('Payment amounts cannot be edited.')
        super().save(*a, **k)


class PaymentItem(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name='items')
    service = models.ForeignKey(Service, on_delete=models.PROTECT)
    name = models.CharField(max_length=100)    # copied at payment time
    price = models.PositiveIntegerField()      # copied at payment time

    def delete(self, *a, **k):
        raise PermissionDenied('Receipt lines cannot be deleted.')


class DayClose(models.Model):
    date = models.DateField(unique=True)
    expected_cash = models.PositiveIntegerField()
    counted_cash = models.PositiveIntegerField()
    difference = models.IntegerField(help_text='Counted cash minus expected cash (TZS)')
    closed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='+')
    closed_at = models.DateTimeField(auto_now_add=True)
    note = models.CharField(max_length=255, blank=True)


class AuditLog(models.Model):
    at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, null=True, on_delete=models.PROTECT, related_name='+')
    action = models.CharField(max_length=30)
    detail = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-at']
