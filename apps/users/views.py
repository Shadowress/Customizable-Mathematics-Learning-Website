from http.client import HTTPResponse

from django.contrib import messages
from django.contrib.auth import get_user_model, login, get_backends, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.contrib.auth.views import LogoutView
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.http import urlsafe_base64_decode
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_exempt

from apps.courses.models import Course, ScheduledCourse
from .forms import CustomSignupForm, ProfileUpdateForm
from .utils import pre_login_redirect, send_email, verify_normal_user, role_required

# Create your views here.
User = get_user_model()
signer = TimestampSigner()


# --- Main Page ---
@pre_login_redirect
def home(request):
    return render(request, "home.html")


# --- Authentication ---
@pre_login_redirect
def user_login(request):
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

            if user.role == "normal":
                return redirect("dashboard")
            elif user.role == "content_manager":
                return redirect("content_manager_dashboard")

        if user is None:
            form.errors.pop("__all__", None)
            form.add_error(None, "Please enter a correct email and password.")

    else:
        form = AuthenticationForm()

    return render(request, "auth/login.html", {"form": form})


@pre_login_redirect
def user_signup(request):
    if request.method == "POST":
        form = CustomSignupForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.is_verified = False
            user.save()

            backend = get_backends()[0]
            login(request, user, backend=backend.__class__.__module__ + "." + backend.__class__.__name__)

            send_email(user, "verification")
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


@login_required
def check_verification_status(request):
    if request.user.is_authenticated and request.user.is_verified:
        return redirect("dashboard")

    return HttpResponse(status=204)


@login_required
@csrf_exempt
def resend_verification_email(request):
    if request.method == "POST":
        send_email(request.user, "verification")
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
            send_email(user, "password_reset")
            request.session["password_reset_email"] = email
            request.session.set_expiry(300)

        return redirect("verify_password_reset_page")

    if request.method == "POST":
        email = request.POST.get("email")

        if not email:
            messages.error(request, "Please enter a valid email address.")
            return redirect("password_reset")

        user = User.objects.filter(email=email).first()

        if user and user.socialaccount_set.filter(provider="google").exists():
            messages.error(request, "Password reset is not available for Google accounts. Please log in using Google.")
            return redirect("homepage")

        if user:
            send_email(user, "password_reset")
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

        send_email(user, "password_reset")

        return JsonResponse({"message": "Password reset verification email has been resent."})

    except User.DoesNotExist:
        return JsonResponse({"error": "User with this email does not exist."}, status=404)


# --- Dashboard Views ---
@role_required(['normal'])
@verify_normal_user
def dashboard(request):
    query = request.GET.get('q', '')
    saved_only = request.GET.get('saved_only') == 'true'
    courses_qs = Course.objects.filter(status='published')

    if query:
        courses_qs = courses_qs.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )

    user_saved_courses = request.user.saved_courses.all()
    user_completed_courses = request.user.completed_courses.all()

    if saved_only:
        courses_qs = courses_qs.filter(id__in=user_saved_courses.values_list('id', flat=True))

    courses = []
    for course in courses_qs:
        courses.append({
            "title": course.title,
            "description": course.description,
            "slug": course.slug,
            "difficulty": course.get_difficulty_display(),
            "is_saved": course in user_saved_courses,
            "is_completed": course in user_completed_courses,
        })

    scheduled_courses = ScheduledCourse.objects.filter(
        user=request.user,
        scheduled_time__gte=timezone.now()
    ).select_related('course').order_by('scheduled_time')

    return render(
        request,
        "dashboard/dashboard.html",
        {
            "normal_user_header_included": True,
            "courses": courses,
            "query": query,
            "saved_only": saved_only,
            "scheduled_courses": scheduled_courses,
        }
    )


@role_required(['normal'])
@verify_normal_user
def profile(request):
    form = ProfileUpdateForm(instance=request.user)

    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, instance=request.user)

        if form.is_valid():
            form.save()
            return redirect("profile")

    published_completed_courses = request.user.completed_courses.filter(status='published')
    user_saved_courses = request.user.saved_courses.all()
    user_completed_courses = request.user.completed_courses.all()

    return render(request, "dashboard/profile.html", {
        "normal_user_header_included": True,
        "form": form,
        "published_completed_courses": published_completed_courses,
        "saved_courses": user_saved_courses,
        "completed_courses": user_completed_courses,
    })


@role_required(['normal'])
@verify_normal_user
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


@role_required(['content_manager'])
def content_manager_dashboard(request):
    query = request.GET.get('q', '')

    published_courses = Course.objects.filter(status='published')
    draft_courses = Course.objects.filter(status='draft', created_by=request.user)

    if query:
        search_filter = Q(title__icontains=query) | Q(description__icontains=query)
        published_courses = published_courses.filter(search_filter)
        draft_courses = draft_courses.filter(search_filter)

    return render(
        request,
        "dashboard/content_manager_dashboard.html",
        {
            "content_manager_header_included": True,
            "published_courses": published_courses,
            "draft_courses": draft_courses,
            "query": query
        }
    )
