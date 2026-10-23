from django.db import migrations


def forward(apps, schema_editor):
    Patient = apps.get_model("reception", "Patient")
    Visit = apps.get_model("reception", "Visit")
    patients = {}
    for visit in Visit.objects.all().order_by("id"):
        name = visit.name or " ".join(value for value in (visit.first_name, visit.second_name) if value).strip()
        key = (name, visit.phone, visit.sex)
        patient = patients.get(key)
        if patient is None:
            patient = Patient.objects.create(name=name, phone=visit.phone, sex=visit.sex, created_by_id=visit.created_by_id)
            patients[key] = patient
        visit.patient_id = patient.pk
        visit.save(update_fields=["patient"])


def reverse(apps, schema_editor):
    apps.get_model("reception", "Visit").objects.update(patient=None)


class Migration(migrations.Migration):
    dependencies = [("reception", "0007_patient_visit_patient_nullable")]
    operations = [migrations.RunPython(forward, reverse)]
