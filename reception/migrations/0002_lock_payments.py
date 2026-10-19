from django.db import migrations


FORWARD_SQL = """
CREATE TRIGGER reception_payment_no_delete
BEFORE DELETE ON reception_payment
BEGIN
    SELECT RAISE(ABORT, 'Payments cannot be deleted');
END;

CREATE TRIGGER reception_paymentitem_no_delete
BEFORE DELETE ON reception_paymentitem
BEGIN
    SELECT RAISE(ABORT, 'Payment items cannot be deleted');
END;

CREATE TRIGGER reception_auditlog_no_delete
BEFORE DELETE ON reception_auditlog
BEGIN
    SELECT RAISE(ABORT, 'Audit logs cannot be deleted');
END;

CREATE TRIGGER reception_paymentitem_no_update
BEFORE UPDATE ON reception_paymentitem
BEGIN
    SELECT RAISE(ABORT, 'Payment items cannot be changed');
END;

CREATE TRIGGER reception_auditlog_no_update
BEFORE UPDATE ON reception_auditlog
BEGIN
    SELECT RAISE(ABORT, 'Audit logs cannot be changed');
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
DROP TRIGGER IF EXISTS reception_paymentitem_no_delete;
DROP TRIGGER IF EXISTS reception_auditlog_no_delete;
DROP TRIGGER IF EXISTS reception_paymentitem_no_update;
DROP TRIGGER IF EXISTS reception_auditlog_no_update;
DROP TRIGGER IF EXISTS reception_payment_lock_financial_fields;
"""


class Migration(migrations.Migration):
    dependencies = [("reception", "0001_initial")]

    operations = [migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)]
