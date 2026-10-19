from django.core.management.base import BaseCommand

from reception.password_recovery import reset_password


class Command(BaseCommand):
    help = "Reset a user's password using the local console."

    def add_arguments(self, parser):
        parser.add_argument("username")

    def handle(self, *args, **options):
        reset_password(options["username"])
        self.stdout.write(self.style.SUCCESS("Password reset complete."))
