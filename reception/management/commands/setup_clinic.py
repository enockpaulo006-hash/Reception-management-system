from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from reception.models import Service


PLACEHOLDER_SERVICES = [
    ("Consultation", "CONSULT", 5000),
    ("Malaria test (mRDT)", "TEST", 3000),
    ("Blood sugar", "TEST", 2000),
    ("Urine test", "TEST", 2000),
    ("Pregnancy test", "TEST", 2000),
]


class Command(BaseCommand):
    help = "Create clinic roles and initial placeholder services."

    def handle(self, *args, **options):
        Group.objects.get_or_create(name="Owner")
        Group.objects.get_or_create(name="Receptionist")

        if not Service.objects.exists():
            Service.objects.bulk_create(
                [
                    Service(name=name, kind=kind, price=price)
                    for name, kind, price in PLACEHOLDER_SERVICES
                ]
            )
            self.stdout.write(self.style.SUCCESS("Created placeholder services."))
        else:
            self.stdout.write("Services already exist; placeholder services were not changed.")

        self.stdout.write("Replace the placeholder prices in /admin/ before taking payments.")
