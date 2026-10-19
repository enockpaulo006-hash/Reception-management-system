from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("reception", "0003_dayclose_difference")]

    operations = [
        migrations.CreateModel(
            name="Setting",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.CharField(max_length=100, unique=True)),
                ("value", models.CharField(max_length=255)),
            ],
        ),
    ]
