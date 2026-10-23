from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("reception", "0009_visit_patient_required")]
    operations = [migrations.CreateModel(name="ClinicSettings", fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("last_report_open", models.DateField(blank=True, null=True)), ("previous_report_open", models.DateField(blank=True, null=True))])]
