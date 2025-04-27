from functools import wraps

from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.core.signing import TimestampSigner
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.html import format_html
from django.utils.http import urlsafe_base64_encode

signer = TimestampSigner()


def _redirect_user_dashboard(user):
    """
    Redirects the user to their respective dashboard based on their role.
    - Normal users are redirected to dashboard/
    - Content managers are redirected to content_manager_dashboard/
    - Superusers are redirected to homepage/
    """
    if user.role == "normal":
        return redirect("dashboard")
    elif user.role == "content_manager":
        return redirect("content_manager_dashboard")
    return redirect("homepage")


def generate_verification_token(user) -> str:
    user_id_encoded = urlsafe_base64_encode(force_bytes(user.pk))
    signed_token = signer.sign(user_id_encoded)
    return signed_token


def send_email(user, purpose, extra_context=None):
    """Sends a verification, password reset, or scheduled course reminder email with a token."""
    token = generate_verification_token(user)
    current_site = get_current_site(None)

    if purpose == "verification":
        url = f"http://{current_site.domain}{reverse('verify_email', args=[token])}"
        subject = "Verify Your Email"
        message = format_html(
            'Click <a href="{}">this link</a> to verify your email.<br><br>'
            'This link will expire in 5 minutes.', url
        )

    elif purpose == "password_reset":
        url = f"http://{current_site.domain}{reverse('verify_password_reset', args=[token])}"
        subject = "Reset Your Password"
        message = format_html(
            'Click <a href="{}">this link</a> to reset your password.<br><br>'
            'This link will expire in 5 minutes.', url
        )

    elif purpose == "scheduled_course_reminder":
        if not extra_context or "course_title" not in extra_context or "scheduled_time" not in extra_context:
            raise ValueError("Missing extra_context data for scheduled course reminder.")

        course_title = extra_context["course_title"]
        scheduled_time = extra_context["scheduled_time"]

        subject = f"Upcoming Scheduled Course Reminder: {course_title}"
        message = format_html(
            "<p>Hi {},</p>"
            "<p>This is a reminder that you have a scheduled course:</p>"
            "<ul>"
            "<li><strong>Course:</strong> {}</li>"
            "<li><strong>Scheduled Time:</strong> {}</li>"
            "</ul>"
            "<p>Don't miss it!</p>",
            user.get_full_name() or user.username,
            course_title,
            scheduled_time.strftime("%Y-%m-%d %H:%M")
        )

    else:
        raise ValueError("Invalid email purpose")

    email = EmailMessage(subject, message, settings.EMAIL_HOST_USER, [user.email])
    email.content_subtype = "html"
    email.send(fail_silently=False)


# === DECORATORS ===
def pre_login_redirect(view_func):
    """
    Redirect authenticated users away from homepage, login, or signup.
    Superusers are allowed to access these pages.
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        if user.is_authenticated:
            if user.is_superuser:
                return view_func(request, *args, **kwargs)
            return _redirect_user_dashboard(user)
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def role_required(allowed_roles):
    """
    Decorator for authenticated-only views, redirects based on user role.
    Redirects:
    - Not logged in → homepage
    - Superuser → homepage
    - Role not in allowed_roles → own dashboard
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                return redirect("homepage")
            if user.is_superuser:
                return redirect("homepage")
            if user.role not in allowed_roles:
                return _redirect_user_dashboard(user)
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def verify_normal_user(view_func):
    """
    Redirect unverified normal users to email verification page.
    Sends email if not yet verified.
    Skips for other roles.
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        if user.role == "normal" and not user.is_verified:
            send_email(user, "verification")
            return redirect("verify_email_page")
        return view_func(request, *args, **kwargs)

    return _wrapped_view
