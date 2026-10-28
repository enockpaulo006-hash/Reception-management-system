
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from reception.models import Service


# Official service names and prices in TZS.
# Existing services are updated by name; unrelated services are preserved.
SERVICES = [
    ("Consultation fees", "CONSULT", 1000),
    ("Blood slide (BS)", "TEST", 1000),
    ("MRDT", "TEST", 1000),
    ("WIDAL test", "TEST", 2000),
    ("Urinalysis", "TEST", 3000),
    ("Urine", "TEST", 1000),
    ("Stool", "TEST", 1000),
    ("HB", "TEST", 3000),
    ("PITC", "TEST", 2000),
    ("Sickle cell", "TEST", 10000),
    ("Syphilis (VDRL)", "TEST", 2000),
    ("Blood sugar (RBG)", "TEST", 2000),
    ("Hepatitis B", "TEST", 5000),
    ("Blood group", "TEST", 2000),
    ("urine sediment", "TEST", 1000),
    ("Foolblood picture (fbp)", "TEST", 10000),
    ("ESR", "TEST", 2000),
    ("BLeeding time &clothing time", "TEST", 1000),
    ("Upt.", "TEST", 1000),
    ("H.pylori Test", "TEST", 5000),
    ("Uric acid", "TEST", 5000),
]


class Command(BaseCommand):
    help = "Ensure the clinic roles and official services exist."

    def handle(self, *args, **options):
        Group.objects.get_or_create(name="Owner")
        Group.objects.get_or_create(name="Receptionist")

        created_count = 0
        updated_count = 0

        for name, kind, price in SERVICES:
            service = Service.objects.filter(name__iexact=name).first()

            if service is None:
                Service.objects.create(
                    name=name,
                    kind=kind,
                    price=price,
                    active=True,
                )
                created_count += 1
            else:
                changed = (
                    service.kind != kind
                    or service.price != price
                    or not service.active
                )

                if changed:
                    service.kind = kind
                    service.price = price
                    service.active = True
                    service.save(
                        update_fields=["kind", "price", "active"]
                    )
                    updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Service setup complete. Created: {created_count}; "
                f"updated: {updated_count}. Other services were preserved."
            )
        )
