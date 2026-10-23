from django.db import migrations, models


def split_names(apps, schema_editor):
    Patient = apps.get_model("reception", "Patient")
    for patient in Patient.objects.all():
        parts = patient.name.split(maxsplit=1)
        patient.first_name = parts[0] if parts else ""
        patient.second_name = parts[1] if len(parts) > 1 else ""
        patient.save(update_fields=["first_name", "second_name"])


class Migration(migrations.Migration):
    dependencies = [("reception", "0010_clinicsettings_report_dates")]
    operations = [
        migrations.AddField(model_name="patient", name="first_name", field=models.CharField(blank=True, default="", max_length=60)),
        migrations.AddField(model_name="patient", name="second_name", field=models.CharField(blank=True, default="", max_length=60)),
        migrations.RunPython(split_names, migrations.RunPython.noop),
    ]
