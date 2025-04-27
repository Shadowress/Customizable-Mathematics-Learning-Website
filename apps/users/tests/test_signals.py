from allauth.socialaccount.models import SocialAccount, SocialLogin
from allauth.socialaccount.signals import social_account_added
from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class GoogleSignalTest(TestCase):
    def test_google_user_marked_verified_on_social_account_added(self):
        user = User.objects.create_user(username="test", email="test@example.com", password="password")
        social_account = SocialAccount.objects.create(user=user, provider="google", uid="12345")

        sociallogin = SocialLogin(account=social_account, user=user)

        # Trigger signal manually
        social_account_added.send(sender=SocialLogin, request=None, sociallogin=sociallogin)

        user.refresh_from_db()
        self.assertTrue(user.is_verified)
