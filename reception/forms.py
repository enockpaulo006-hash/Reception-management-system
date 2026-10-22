import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, SetPasswordForm, UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import Visit




class VisitForm(forms.ModelForm):
    first_name = forms.CharField(
        label="First name",
        max_length=60,
        required=True,
        widget=forms.TextInput(attrs={"autocomplete": "off"}),
    )

    second_name = forms.CharField(
        label="Second name",
        max_length=60,
        required=True,
        widget=forms.TextInput(attrs={"autocomplete": "off"}),
    )

    physical_address = forms.CharField(
        label="Physical address",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "off"}),
    )
    phone = forms.CharField(
    label="Phone",
    required=False,
    max_length=10,
    min_length=10,
    widget=forms.TextInput(attrs={
        "autocomplete": "off",
        "maxlength": "10",
        "minlength": "10",
        "pattern": r"0[67][0-9]{8}",
        "inputmode": "numeric",
        "oninput": "this.value = this.value.replace(/[^0-9]/g, '').slice(0, 10)",
        "placeholder": "07XXXXXXXX or 06XXXXXXXX",
        "title": "Enter exactly 10 digits starting with 06 or 07",
    }),
)

    class Meta:
        model = Visit
        fields = (
            "first_name",
            "second_name",
            "phone",
            "age",
            "sex",
            "physical_address",
        )
        labels = {
            "phone": "Phone",
            "age": "Age",
            "sex": "Sex",
        }
        widgets = {
            "phone": forms.TextInput(attrs={
                "autocomplete": "off",
                "maxlength": "10",
                "minlength": "10",
                "pattern": "0[67][0-9]{8}",
                "inputmode": "numeric",
                "placeholder": "07XXXXXXXX or 06XXXXXXXX",
                "title": "Enter exactly 10 digits starting with 07 or 06",
            }),
            "age": forms.NumberInput(attrs={"min": 0}),
    
        }

def clean_phone(self):
    phone = self.cleaned_data.get("phone", "").strip()

    if phone and not re.fullmatch(r"0[67]\d{8}", phone):
        raise forms.ValidationError(
            "Phone number must contain exactly 10 digits and start with 06 or 07."
        )

    return phone
        

class ClinicAuthenticationForm(AuthenticationForm):
    """Use clear, role-neutral login feedback for the shared sign-in page."""

    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Incorrect username or password.",
    }

    def clean(self):
        username = self.cleaned_data.get("username")
        if username and User.objects.filter(username=username, is_active=False).exists():
            raise ValidationError("This account is deactivated.")
        return super().clean()


class ReceptionistCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name")


class OwnPasswordChangeForm(PasswordChangeForm):
    pass


class UserPasswordResetForm(SetPasswordForm):
    pass


class SetupForm(forms.Form):
    clinic_name = forms.CharField(max_length=255)
    owner_full_name = forms.CharField(max_length=150)
    owner_username = forms.CharField(max_length=150)
    owner_password1 = forms.CharField(widget=forms.PasswordInput)
    owner_password2 = forms.CharField(widget=forms.PasswordInput)
    receptionist_username = forms.CharField(max_length=150, required=False)
    receptionist_password = forms.CharField(widget=forms.PasswordInput, required=False)

    def clean(self):
        cleaned_data = super().clean()
        owner_password1 = cleaned_data.get("owner_password1")
        owner_password2 = cleaned_data.get("owner_password2")
        owner_username = cleaned_data.get("owner_username")
        owner_full_name = cleaned_data.get("owner_full_name")
        receptionist_username = cleaned_data.get("receptionist_username", "").strip()
        receptionist_password = cleaned_data.get("receptionist_password")

        if owner_password1 and owner_password2 and owner_password1 != owner_password2:
            self.add_error("owner_password2", "The passwords do not match.")
        elif owner_password1:
            validate_password(
                owner_password1,
                User(username=owner_username, first_name=owner_full_name),
            )

        if receptionist_username or receptionist_password:
            if not receptionist_username:
                self.add_error("receptionist_username", "Enter a receptionist username.")
            elif receptionist_username == owner_username:
                self.add_error("receptionist_username", "The receptionist username must be different from the owner username.")
            if not receptionist_password:
                self.add_error("receptionist_password", "Enter a receptionist password.")
            elif receptionist_username:
                validate_password(receptionist_password, User(username=receptionist_username))
        return cleaned_data
