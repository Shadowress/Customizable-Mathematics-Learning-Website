from http.client import HTTPResponse

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, get_backends, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.contrib.auth.views import LogoutView
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.mail import EmailMessage
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.html import format_html
from django.utils.http import urlsafe_base64_decode
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_exempt

from apps.courses.models import Course
from .forms import CustomSignupForm, ProfileUpdateForm
from .permissions import normal_user_required, content_manager_required
from .utils import generate_verification_token

# Create your views here.
User = get_user_model()
signer = TimestampSigner()


# --- Main Page ---
def home(request) -> HTTPResponse:
    redirection = _redirect_authenticated_user(request.user)

    if redirection:
        return redirection

    return render(request, "home.html")


# --- Authentication ---
def user_login(request):
    redirection = _redirect_authenticated_user(request.user)
    if redirection:
        return redirection

    if request.method == "POST":
        post_data = request.POST.copy()
        email = post_data.get("username", "").strip().lower()
        post_data["username"] = email
        form = AuthenticationForm(request, data=post_data)

        try:
            user = User.objects.get(email=email)

            if not user.has_usable_password():
                form.errors.pop("__all__", None)
                form.add_error(None, "This email is registered with Google. Please log in using Google.")
                return render(request, "auth/login.html", {"form": form})
        except User.DoesNotExist:
            user = None

        if form.is_valid():
            user = form.get_user()

            if user.is_superuser:
                form.errors.pop("__all__", None)
                form.add_error(None, "Please enter a correct email and password.")
                return render(request, "auth/login.html", {"form": form})

            backend = get_backends()[0]
            login(request, user, backend=backend.__class__.__module__ + "." + backend.__class__.__name__)

            if not user.is_verified:
                _send_email(user, "verification")
                return redirect("verify_email_page")

            return _redirect_user_dashboard(user)

        if user is None:
            form.errors.pop("__all__", None)
            form.add_error(None, "Please enter a correct email and password.")

    else:
        form = AuthenticationForm()

    return render(request, "auth/login.html", {"form": form})


def user_signup(request):
    redirection = _redirect_authenticated_user(request.user)

    if redirection:
        return redirection

    if request.method == "POST":
        form = CustomSignupForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.is_verified = False
            user.save()

            backend = get_backends()[0]
            login(request, user, backend=backend.__class__.__module__ + "." + backend.__class__.__name__)

            _send_email(user, "verification")
            return redirect("verify_email_page")

    else:
        form = CustomSignupForm()

    return render(request, "auth/signup.html", {"form": form})


class CustomLogoutView(LogoutView):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        storage = messages.get_messages(request)
        list(storage)
        return super().dispatch(request, *args, **kwargs)


# --- Email Verification ---
@login_required
def verify_email_page(request):
    return render(request, "auth/verify_email.html")


@login_required
def verify_email(request, token):
    try:
        unsigned_data = signer.unsign(token, max_age=300)
        user_id = urlsafe_base64_decode(unsigned_data).decode()
        user = User.objects.get(pk=user_id)

        user.is_verified = True
        user.save()

        return HttpResponse(
            mark_safe("""
                <script>
                    window.close();
                </script>
            """)
        )

    except (BadSignature, SignatureExpired, User.DoesNotExist):
        return HttpResponse(
            mark_safe("""
                <script>
                    window.close();
                </script>
            """)
        )


def check_verification_status(request):
    if request.user.is_authenticated and request.user.is_verified:
        return _redirect_user_dashboard(request.user)

    return HttpResponse(status=204)


@login_required
@csrf_exempt
def resend_verification_email(request):
    if request.method == "POST":
        _send_email(request.user, "verification")
        return JsonResponse({"message": "Verification email resent."})

    return JsonResponse({"error": "Invalid request."}, status=400)


# --- Password Reset ---
def password_reset_request(request):
    """Handles password reset requests for both logged-in and logged-out users."""
    request.session.pop("password_reset_verified_user", None)

    if request.user.is_authenticated:
        if request.user.socialaccount_set.filter(provider="google").exists():
            messages.error(request, "Password reset is not available for Google accounts. Please log in using Google.")
            return redirect("homepage")

        email = request.user.email
        user = User.objects.filter(email=email).first()

        if user:
            _send_email(user, "password_reset")
            request.session["password_reset_email"] = email
            request.session.set_expiry(300)

        return redirect("verify_password_reset_page")

    if request.method == "POST":
        email = request.POST.get("email")

        if not email:
            messages.error(request, "Please enter a valid email address.")
            return redirect("password_reset_request")

        user = User.objects.filter(email=email).first()

        if user and user.socialaccount_set.filter(provider="google").exists():
            messages.error(request, "Password reset is not available for Google accounts. Please log in using Google.")
            return redirect("homepage")

        if user:
            _send_email(user, "password_reset")
            request.session["password_reset_email"] = email
            request.session.set_expiry(300)

        return redirect("verify_password_reset_page")

    return render(request, "auth/password_reset/request.html")


def verify_password_reset_page(request):
    """Page displayed after submitting the password reset request."""
    if not request.session.get("password_reset_email"):
        return redirect("homepage")

    return render(request, "auth/password_reset/verification.html")


def verify_password_reset(request, token):
    """Handles password reset form submission."""
    try:
        unsigned_data = signer.unsign(token, max_age=300)
        user_id = urlsafe_base64_decode(unsigned_data).decode()
        user = User.objects.get(pk=user_id)

        request.session.flush()
        request.session.cycle_key()

        request.session["password_reset_verified_user"] = user.id
        request.session.set_expiry(300)

        return HttpResponse(
            mark_safe("""
                    <script>
                        window.close();
                    </script>
                """)
        )

    except (BadSignature, SignatureExpired, User.DoesNotExist):
        return HttpResponse(
            mark_safe("""
                    <script>
                        window.close();
                    </script>
                """)
        )


def password_reset_form(request):
    user_id = request.session.get("password_reset_verified_user")

    if not user_id:
        return redirect("homepage")

    try:
        user = User.objects.get(pk=user_id)

    except User.DoesNotExist:
        return redirect("homepage")

    if request.method == "POST":
        form = SetPasswordForm(user, request.POST)

        if form.is_valid():
            form.save()

            if request.user.is_authenticated:
                logout(request)

            request.session.flush()
            return redirect("login")

    else:
        form = SetPasswordForm(user)

    return render(request, "auth/password_reset/form.html", {"form": form})


def check_password_reset_verification(request):
    user_id = request.session.get("password_reset_verified_user")

    if user_id:
        return JsonResponse({"status": "verified", "redirect_url": f"/password-reset/new-password/"})
    else:
        return JsonResponse({"status": "pending"})


@csrf_exempt
def resend_password_reset_verification(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method."}, status=400)

    email = request.session.get("password_reset_email")

    if not email:
        return JsonResponse({"error": "Email is required."}, status=400)

    try:
        user = User.objects.get(email=email)

        if not user.is_active:
            return JsonResponse({"error": "User account is not active."}, status=400)

        _send_email(user, "password_reset")

        return JsonResponse({"message": "Password reset verification email has been resent."})

    except User.DoesNotExist:
        return JsonResponse({"error": "User with this email does not exist."}, status=404)


# --- Dashboard Views ---
@user_passes_test(normal_user_required, login_url="homepage")
def dashboard(request) -> HTTPResponse:
    courses = Course.objects.all()
    return render(request, "dashboard/dashboard.html",  {"normal_user_header_included": True, "courses": courses})


@user_passes_test(normal_user_required, login_url="homepage")
def profile(request):
    form = ProfileUpdateForm(instance=request.user)

    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, instance=request.user)

        if form.is_valid():
            form.save()
            return redirect("profile")

    return render(request, "dashboard/profile.html", {"normal_user_header_included": True, "form": form})


@user_passes_test(normal_user_required, login_url="homepage")
def profile_picture_upload(request):
    if request.method == "POST" and request.FILES.get("profile_picture"):
        user = request.user
        file = request.FILES["profile_picture"]

        # Define a fixed filename format based on user ID
        file_name = f"profile_pictures/{user.id}_profile.jpg"

        # Delete old file before saving new one (if exists)
        if user.profile_picture:
            default_storage.delete(user.profile_picture.path)

        # Save new image
        path = default_storage.save(file_name, ContentFile(file.read()))

        # Ensure the database URL remains the same (avoid duplicates)
        user.profile_picture = file_name
        user.save()

        return redirect("profile")  # Reload page to apply changes

    return redirect("profile")


@user_passes_test(content_manager_required, login_url="homepage")
def content_manager_dashboard(request) -> HTTPResponse:
    courses = Course.objects.all()
    return render(request, "dashboard/content_manager_dashboard.html",
                  {"content_manager_header_included": True, "courses": courses})


# --- Private Methods ---
def _redirect_authenticated_user(user):
    """
    Redirect authenticated users based on their account status.
    - Superusers can access home, login, or signup pages.
    - Active users are redirected to their respective dashboards.
    - Inactive users are redirected to the email verification page.
    """
    if not user.is_authenticated:
        return None

    if user.is_superuser:
        return None

    if not user.is_verified:
        _send_email(user, "verification")
        return redirect("verify_email_page")

    return _redirect_user_dashboard(user)


def _redirect_user_dashboard(user):
    """Redirect users based on their role."""
    if user.role == "normal":
        return redirect("dashboard")

    elif user.role == "content_manager":
        return redirect("content_manager_dashboard")

    raise PermissionDenied("Invalid user role.")


def _send_email(user, purpose):
    """Sends a verification or password reset email with a token."""
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

    else:
        raise ValueError("Invalid email purpose")

    email = EmailMessage(subject, message, settings.EMAIL_HOST_USER, [user.email])
    email.content_subtype = "html"  # Set email to be HTML formatted
    email.send(fail_silently=False)
