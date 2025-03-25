from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.forms.widgets import DateInput

User = get_user_model()


class CustomSignupForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def clean_email(self):
        """Convert email to lowercase and check if it already exists."""
        email = self.cleaned_data.get("email", "").strip().lower()
        existing_user = User.objects.filter(email=email).first()

        if not existing_user:
            return email

        if not existing_user.has_usable_password():
            raise forms.ValidationError("This email is registered with Google. Please log in using Google.")

        raise forms.ValidationError("An account with this email already exists.")

    def save(self, commit=True):
        """Ensure the email is always stored in lowercase."""
        user = super().save(commit=False)
        user.email = user.email.lower()

        if commit:
            user.save()

        return user


class ProfileUpdateForm(forms.ModelForm):
    date_of_birth = forms.DateField(
        widget=DateInput(attrs={'type': 'date'}),
        required=False
    )

    class Meta:
        model = User
        fields = ['username', 'date_of_birth']
