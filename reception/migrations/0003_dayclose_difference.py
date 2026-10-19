from django.db import migrations, models


def populate_differences(apps, schema_editor):
    DayClose = apps.get_model("reception", "DayClose")
    for day_close in DayClose.objects.all():
        day_close.difference = day_close.counted_cash - day_close.expected_cash
        day_close.save(update_fields=["difference"])


class Migration(migrations.Migration):
    dependencies = [("reception", "0002_lock_payments")]

    operations = [
        migrations.AddField(
            model_name="dayclose",
            name="difference",
            field=models.IntegerField(default=0, help_text="Counted cash minus expected cash (TZS)"),
            preserve_default=False,
        ),
        migrations.RunPython(populate_differences, migrations.RunPython.noop),
    ]
