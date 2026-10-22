
from django.db import migrations


FORWARD_SQL = """
CREATE TRIGGER reception_payment_no_delete
BEFORE DELETE ON reception_payment
BEGIN
    SELECT RAISE(ABORT, 'Payments cannot be deleted');
END;

CREATE TRIGGER reception_payment_lock_financial_fields
BEFORE UPDATE ON reception_payment
WHEN OLD.total IS NOT NEW.total
  OR OLD.receipt_no IS NOT NEW.receipt_no
  OR OLD.visit_id IS NOT NEW.visit_id
  OR OLD.received_by_id IS NOT NEW.received_by_id
  OR OLD.paid_at IS NOT NEW.paid_at
BEGIN
    SELECT RAISE(ABORT, 'Payment financial fields cannot be changed');
END;
"""

REVERSE_SQL = """
DROP TRIGGER IF EXISTS reception_payment_no_delete;
DROP TRIGGER IF EXISTS reception_payment_lock_financial_fields;
"""


class Migration(migrations.Migration):

    dependencies = [
        ("reception", "0005_visit_first_name_visit_physical_address_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="payment",
            name="void_reason",
        ),
        migrations.RemoveField(
            model_name="payment",
            name="voided",
        ),
        migrations.RemoveField(
            model_name="payment",
            name="voided_at",
        ),
        migrations.RemoveField(
            model_name="payment",
            name="voided_by",
        ),
        migrations.RunSQL(
            sql=FORWARD_SQL,
            reverse_sql=REVERSE_SQL,
        ),
    ]
