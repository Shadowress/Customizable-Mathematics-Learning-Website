from io import BytesIO
from unittest.mock import patch

from PIL import Image
from allauth.socialaccount.models import SocialApp
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.contrib.sites.models import Site
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.signing import TimestampSigner
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.courses.models import Course, ScheduledCourse

User = get_user_model()
signer = TimestampSigner()


class AuthViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.login_url = reverse("login")
        self.signup_url = reverse("signup")
        self.home_url = reverse("homepage")
        self.password = "securepass123"

        self.normal_user = User.objects.create_user(
            email="normal@example.com",
            password=self.password,
            role="normal",
            is_verified=True,
        )

        self.cm_user = User.objects.create_user(
            email="cm@example.com",
            password=self.password,
            role="content_manager",
            is_verified=True,
        )

        self.google_user = User.objects.create(
            email="google@example.com",
            role="normal",
            is_verified=True,
        )
        self.google_user.set_unusable_password()
        self.google_user.save()

        site, _ = Site.objects.get_or_create(domain="example.com", defaults={"name": "example"})
        self.social_app = SocialApp.objects.create(
            provider="google",
            name="Test Google",
            client_id="test-client-id",
            secret="test-secret",
        )
        self.social_app.sites.set([site])

    # --- Login View Tests ---

    def test_login_view_get(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "auth/login.html")

    def test_login_view_invalid_credentials(self):
        response = self.client.post(self.login_url, {
            "username": "wrong@example.com",
            "password": "wrongpass"
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter a correct email and password.")

    def test_login_view_google_account(self):
        response = self.client.post(self.login_url, {
            "username": "google@example.com",
            "password": "any"
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This email is registered with Google. Please log in using Google.")

    def test_login_redirects_normal_user_to_dashboard(self):
        response = self.client.post(self.login_url, {
            "username": "normal@example.com",
            "password": self.password
        })
        self.assertRedirects(response, reverse("dashboard"))

    def test_login_redirects_content_manager_to_dashboard(self):
        response = self.client.post(self.login_url, {
            "username": "cm@example.com",
            "password": self.password
        })
        self.assertRedirects(response, reverse("content_manager_dashboard"))

    # --- Signup View Tests ---

    def test_signup_view_get(self):
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "auth/signup.html")

    def test_signup_view_post_valid(self):
        response = self.client.post(self.signup_url, {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "StrongPass456",
            "password2": "StrongPass456"
        })

        self.assertRedirects(response, reverse("verify_email_page"))
        self.assertTrue(User.objects.filter(email="newuser@example.com").exists())

        user = User.objects.get(email="newuser@example.com")
        self.assertEqual(user.role, "normal")
        self.assertFalse(user.is_verified)


class EmailVerificationViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="user", email="user@example.com", password="testpass123")
        self.user.is_verified = False
        self.user.save()

        self.login = self.client.login(email="user@example.com", password="testpass123")
        self.verify_email_url = reverse("verify_email_page")
        self.resend_url = reverse("resend_verification_email")
        self.check_url = reverse("check_verification_status")

    def test_verify_email_page_authenticated(self):
        response = self.client.get(self.verify_email_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "auth/verify_email.html")

    def test_verify_email_page_anonymous(self):
        self.client.logout()
        response = self.client.get(self.verify_email_url)
        self.assertRedirects(response, f"/?next={self.verify_email_url}")

    def test_verify_email_with_valid_token(self):
        user_id_encoded = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = signer.sign(user_id_encoded)

        url = reverse("verify_email", kwargs={"token": token})
        response = self.client.get(url)
        self.user.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.user.is_verified)
        self.assertIn("window.close();", response.content.decode())

    def test_verify_email_with_invalid_token(self):
        url = reverse("verify_email", kwargs={"token": "invalid-token"})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("window.close();", response.content.decode())

    def test_check_verification_status_verified_user(self):
        self.user.is_verified = True
        self.user.save()
        response = self.client.get(self.check_url)
        self.assertEqual(response.status_code, 302)  # Should redirect

    def test_check_verification_status_unverified_user(self):
        response = self.client.get(self.check_url)
        self.assertEqual(response.status_code, 204)

    def test_resend_verification_email_post(self):
        self.client.login(email="user@example.com", password="testpass123")
        with patch("apps.users.views.send_email") as mock_send_email:
            response = self.client.post(self.resend_url)
            mock_send_email.assert_called_once()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["message"], "Verification email resent.")

    def test_resend_verification_email_get(self):
        response = self.client.get(self.resend_url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Invalid request.")


class PasswordResetViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email="user@example.com", password="testpass123")
        self.reset_url = reverse("password_reset")
        self.verify_page_url = reverse("verify_password_reset_page")
        self.reset_form_url = reverse("password_reset_form")
        self.check_verification_url = reverse("check_password_reset_verification")
        self.resend_verification_url = reverse("resend_password_reset_verification")

        site, created = Site.objects.get_or_create(domain='example.com', defaults={'name': 'example'})
        self.social_app = SocialApp.objects.create(
            provider='google',
            name='Test Google',
            client_id='test-client-id',
            secret='test-secret',
        )
        self.social_app.sites.set([site])
        self.login_url = '/login/'

    def test_password_reset_request_post_valid_email(self):
        with patch("apps.users.views.send_email") as mock_send_email:
            response = self.client.post(self.reset_url, {"email": self.user.email})
            self.assertRedirects(response, self.verify_page_url)
            mock_send_email.assert_called_once()

    def test_password_reset_request_post_empty_email(self):
        response = self.client.post(self.reset_url, {"email": ""}, follow=True)
        self.assertRedirects(response, self.reset_url)
        messages = list(get_messages(response.wsgi_request))
        self.assertIn("Please enter a valid email address.", [m.message for m in messages])

    def test_password_reset_request_logged_in_non_google_user(self):
        self.client.login(email="user@example.com", password="testpass123")
        with patch("apps.users.views.send_email") as mock_send_email:
            response = self.client.get(self.reset_url)
            self.assertRedirects(response, self.verify_page_url)
            mock_send_email.assert_called_once()

    def test_verify_password_reset_page_without_session(self):
        response = self.client.get(self.verify_page_url)
        self.assertRedirects(response, reverse("homepage"))

    def test_verify_password_reset_valid_token(self):
        user_id_encoded = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = signer.sign(user_id_encoded)
        url = reverse("verify_password_reset", kwargs={"token": token})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("window.close();", response.content.decode())

        # Ensure session contains user ID
        session_user_id = self.client.session.get("password_reset_verified_user")
        self.assertEqual(session_user_id, self.user.pk)

    def test_verify_password_reset_invalid_token(self):
        url = reverse("verify_password_reset", kwargs={"token": "invalid-token"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("window.close();", response.content.decode())

    def test_password_reset_form_valid_post(self):
        session = self.client.session
        session["password_reset_verified_user"] = self.user.pk
        session.save()

        response = self.client.post(self.reset_form_url, {
            "new_password1": "newStrongPassword123",
            "new_password2": "newStrongPassword123",
        })
        self.assertRedirects(response, reverse("login"))

        # Confirm password actually updated
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newStrongPassword123"))

    def test_password_reset_form_without_session(self):
        response = self.client.get(self.reset_form_url)
        self.assertRedirects(response, reverse("homepage"))

    def test_check_password_reset_verification_pending(self):
        response = self.client.get(self.check_verification_url)
        self.assertEqual(response.json()["status"], "pending")

    def test_check_password_reset_verification_verified(self):
        session = self.client.session
        session["password_reset_verified_user"] = self.user.pk
        session.save()

        response = self.client.get(self.check_verification_url)
        self.assertEqual(response.json()["status"], "verified")
        self.assertIn("/password-reset/new-password/", response.json()["redirect_url"])

    def test_resend_password_reset_verification_post(self):
        session = self.client.session
        session["password_reset_email"] = self.user.email
        session.save()

        with patch("apps.users.views.send_email") as mock_send_email:
            response = self.client.post(self.resend_verification_url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["message"], "Password reset verification email has been resent.")
            mock_send_email.assert_called_once()

    def test_resend_password_reset_verification_get_invalid(self):
        response = self.client.get(self.resend_verification_url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Invalid request method.")

    def test_resend_password_reset_verification_no_email(self):
        response = self.client.post(self.resend_verification_url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Email is required.")


class DashboardViewsTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Create a normal user
        self.normal_user = User.objects.create_user(
            email='normal@example.com',
            username='normaluser',
            password='testpass',
            role='normal',
            is_verified=True
        )
        self.normal_user.is_active = True
        self.normal_user.save()

        # Create a content manager user
        self.manager_user = User.objects.create_user(
            email='content_manager@example.com',
            username='manageruser',
            password='testpass',
            role='content_manager'
        )
        self.manager_user.is_active = True
        self.manager_user.save()

    def test_dashboard_access_by_normal_user(self):
        self.client.login(email='normal@example.com', password='testpass')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/dashboard.html")

    def test_dashboard_access_by_content_manager(self):
        self.client.login(email='content_manager@example.com', password='testpass')
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse("content_manager_dashboard"))

    def test_profile_view_get(self):
        self.client.login(email='normal@example.com', password='testpass')
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/profile.html")

    def test_profile_view_post_valid_data(self):
        self.client.login(email='normal@example.com', password='testpass')
        response = self.client.post(reverse("profile"), {
            "username": "normaluser",  # assuming username is editable
            "email": "newemail@example.com"
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("profile"))

    def test_profile_picture_upload(self):
        self.client.login(email='normal@example.com', password='testpass')

        image = BytesIO()
        Image.new('RGB', (100, 100)).save(image, 'JPEG')
        image.seek(0)

        uploaded = SimpleUploadedFile("test.jpg", image.read(), content_type="image/jpeg")
        response = self.client.post(reverse("profile_picture_upload"), {"profile_picture": uploaded})
        self.assertRedirects(response, reverse("profile"))

    def test_content_manager_dashboard_access_by_manager(self):
        self.client.login(email='content_manager@example.com', password='testpass')
        response = self.client.get(reverse('content_manager_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/content_manager_dashboard.html")

    def test_content_manager_dashboard_denied_for_normal_user(self):
        self.client.login(email='normal@example.com', password='testpass')
        response = self.client.get(reverse('content_manager_dashboard'))
        self.assertRedirects(response, reverse("dashboard"))

    def test_dashboard_filters_saved_only(self):
        self.client.login(email='normal@example.com', password='testpass')
        course = Course.objects.create(
            title="Test Course",
            description="A test course.",
            difficulty=Course.JUNIOR,
            estimated_completion_time=30,  # in minutes
            status="published"
        )
        self.normal_user.saved_courses.add(course)

        response = self.client.get(reverse("dashboard"), {"saved_only": "true"})
        self.assertContains(response, "Test Course")

    def test_scheduled_courses_display(self):
        self.client.login(email='normal@example.com', password='testpass')
        course = Course.objects.create(
            title="Future Course",
            description="A scheduled test course.",
            difficulty=Course.JUNIOR,
            estimated_completion_time=45,
            status="published"
        )
        ScheduledCourse.objects.create(user=self.normal_user, course=course,
                                       scheduled_time=timezone.now() + timezone.timedelta(days=1))
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "Future Course")
