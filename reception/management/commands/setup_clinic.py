
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from reception.models import Service


# The only approved active services and their prices in TZS.
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
    help = (
        "Synchronize active clinic services with the approved service list."
    )

    def handle(self, *args, **options):
        # Ensure the required user groups exist.
        Group.objects.get_or_create(name="Owner")
        Group.objects.get_or_create(name="Receptionist")

        created_count = 0
        updated_count = 0
        deactivated_count = 0

        # Create missing services and correct existing approved services.
        for name, kind, price in SERVICES:
            matches = Service.objects.filter(
                name__iexact=name
            ).order_by("id")

            service = matches.first()

            if service is None:
                Service.objects.create(
                    name=name,
                    kind=kind,
                    price=price,
                    active=True,
                )
                created_count += 1
                continue

            changed = (
                service.name != name
                or service.kind != kind
                or service.price != price
                or not service.active
            )

            if changed:
                service.name = name
                service.kind = kind
                service.price = price
                service.active = True
                service.save(
                    update_fields=[
                        "name",
                        "kind",
                        "price",
                        "active",
                    ]
                )
                updated_count += 1

            # Deactivate duplicate records with the same approved name.
            for duplicate in matches.exclude(pk=service.pk):
                if duplicate.active:
                    duplicate.active = False
                    duplicate.save(update_fields=["active"])
                    deactivated_count += 1

        # Deactivate every other service.
        # Historical records are preserved; nothing is deleted.
        approved_names = {
            name.casefold() for name, _, _ in SERVICES
        }

        for service in Service.objects.filter(active=True):
            if service.name.casefold() not in approved_names:
                service.active = False
                service.save(update_fields=["active"])
                deactivated_count += 1

        active_count = Service.objects.filter(active=True).count()

        self.stdout.write(
            self.style.SUCCESS(
                "Service synchronization complete. "
                f"Created: {created_count}; "
                f"updated: {updated_count}; "
                f"deactivated: {deactivated_count}; "
                f"active services: {active_count}."
            )
        )

        if active_count != len(SERVICES):
            self.stdout.write(
                self.style.WARNING(
                    f"Expected {len(SERVICES)} active services, "
                    f"but found {active_count}. "
                    "Check for duplicate service records."
                )
            )
