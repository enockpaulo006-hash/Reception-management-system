import getpass

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.management.base import CommandError

from .services import log


def reset_password(username, input_func=None):
    """Interactively reset a local user's password without displaying it."""
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist as error:
        raise CommandError(f"User '{username}' does not exist.") from error

    prompt = input_func or getpass.getpass
    password = prompt("New password: ")
    confirmation = prompt("Confirm new password: ")
    if password != confirmation:
        raise CommandError("The passwords do not match.")
    try:
        validate_password(password, user)
    except Exception as error:
        raise CommandError(" ".join(error.messages)) from error

    user.set_password(password)
    user.save(update_fields=["password"])
    log(user, "PASSWORD_RESET", "Password reset using local recovery")
