import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("reception", "0006_remove_payment_void_reason_remove_payment_voided_and_more")]
    operations = [
        migrations.CreateModel(name="Patient", fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("name", models.CharField(max_length=120)), ("phone", models.CharField(blank=True, max_length=20)), ("sex", models.CharField(choices=[("M", "Male"), ("F", "Female")], max_length=1)), ("created_at", models.DateTimeField(auto_now_add=True)), ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="+", to=settings.AUTH_USER_MODEL))]),
        migrations.AddField(model_name="visit", name="patient", field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name="visits", to="reception.patient")),
    ]
