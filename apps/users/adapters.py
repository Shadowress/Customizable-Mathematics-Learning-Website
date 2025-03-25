import os
import urllib.request

from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect

User = get_user_model()


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Prevent users from logging in with Google if their email was originally registered using email/password.
        """
        email = sociallogin.user.email.lower()

        if not email:
            return

        existing_user = User.objects.filter(email=email).first()

        if existing_user and existing_user.has_usable_password():
            messages.error(
                request,
                "This email is already registered with an email and password. Please log in using email."
            )
            raise ImmediateHttpResponse(HttpResponseRedirect("/login/"))

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)

        if sociallogin.account.provider == "google":
            user.is_verified = True
            google_data = sociallogin.account.extra_data
            profile_picture_url = google_data.get("picture")

            if profile_picture_url:
                filename = f"{user.id}_profile.jpg"
                profile_pictures_path = os.path.join(settings.MEDIA_ROOT, "profile_pictures")
                os.makedirs(profile_pictures_path, exist_ok=True)
                response = urllib.request.urlopen(profile_picture_url)
                image_content = response.read()
                full_path = os.path.join(profile_pictures_path, filename)

                with open(full_path, "wb") as f:
                    f.write(image_content)

                user.profile_picture.name = os.path.join("profile_pictures", filename)
                user.save()

        return user
