from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, SetPasswordForm, UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import Visit


class VisitForm(forms.ModelForm):
    class Meta:
        model = Visit
        fields = ("name", "phone", "age", "sex")
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "off"}),
            "phone": forms.TextInput(attrs={"autocomplete": "off"}),
            "age": forms.NumberInput(attrs={"min": 0}),
        }


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
