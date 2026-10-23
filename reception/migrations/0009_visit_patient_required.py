from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("reception", "0008_link_existing_visits_to_patients")]
    operations = [migrations.AlterField(model_name="visit", name="patient", field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="visits", to="reception.patient"))]
