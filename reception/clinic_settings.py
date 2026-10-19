from .models import Setting


CLINIC_NAME_KEY = "clinic_name"
DEFAULT_CLINIC_NAME = "Clinic Reception"


def get_clinic_name():
    return (
        Setting.objects.filter(key=CLINIC_NAME_KEY).values_list("value", flat=True).first()
        or DEFAULT_CLINIC_NAME
    )


def set_clinic_name(name):
    Setting.objects.update_or_create(
        key=CLINIC_NAME_KEY,
        defaults={"value": name.strip()},
    )
