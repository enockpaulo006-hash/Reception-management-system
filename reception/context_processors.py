from .clinic_settings import get_clinic_name
from .services import is_owner


def clinic_name(request):
    return {"CLINIC_NAME": get_clinic_name(), "is_owner": is_owner(request.user)}
