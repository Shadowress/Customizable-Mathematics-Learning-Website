from allauth.socialaccount.signals import social_account_added, social_account_updated
from django.dispatch import receiver


@receiver(social_account_added)
@receiver(social_account_updated)
def set_verified_for_google(sender, request, sociallogin, **kwargs):
    """Automatically mark Google users as verified"""
    user = sociallogin.user
    if sociallogin.account.provider == "google":
        user.is_verified = True
        user.save()
