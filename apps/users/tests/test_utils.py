from datetime import datetime, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory
from django.urls import reverse

from apps.users.utils import (
    _redirect_user_dashboard,
    generate_verification_token,
    send_email,
    verify_normal_user,
)

User = get_user_model()


class UtilsTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.normal_user = User.objects.create_user(
            username="normaluser",
            email="normal@example.com",
            password="testpass123",
            role="normal",
            is_verified=False,
        )

        self.manager_user = User.objects.create_user(
            username="manager",
            email="manager@example.com",
            password="testpass123",
            role="content_manager",
            is_verified=True,
        )

    def test_redirect_user_dashboard(self):
        resp = _redirect_user_dashboard(self.normal_user)
        self.assertEqual(resp.url, reverse("dashboard"))

        resp = _redirect_user_dashboard(self.manager_user)
        self.assertEqual(resp.url, reverse("content_manager_dashboard"))

    def test_generate_verification_token_valid(self):
        token = generate_verification_token(self.normal_user)
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 10)

    @patch("apps.users.utils.EmailMessage.send")
    def test_send_email_verification(self, mock_send):
        send_email(self.normal_user, "verification")
        mock_send.assert_called_once()

    @patch("apps.users.utils.EmailMessage.send")
    def test_send_email_password_reset(self, mock_send):
        send_email(self.normal_user, "password_reset")
        mock_send.assert_called_once()

    @patch("apps.users.utils.EmailMessage.send")
    def test_send_email_scheduled_course_reminder(self, mock_send):
        extra_context = {
            "course_title": "Math Basics",
            "scheduled_time": datetime.now() + timedelta(days=1),
        }
        send_email(self.normal_user, "scheduled_course_reminder", extra_context=extra_context)
        mock_send.assert_called_once()

    def test_send_email_invalid_purpose(self):
        with self.assertRaises(ValueError):
            send_email(self.normal_user, "invalid-purpose")

    def test_verify_normal_user_decorator_redirects_unverified_user(self):
        request = self.factory.get("/some-protected-page")
        request.user = self.normal_user

        @verify_normal_user
        def fake_view(req):
            return "ACCESS GRANTED"

        response = fake_view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("verify_email_page"))

    def test_verify_normal_user_decorator_skips_verified_user(self):
        self.normal_user.is_verified = True
        self.normal_user.save()

        request = self.factory.get("/some-protected-page")
        request.user = self.normal_user

        @verify_normal_user
        def fake_view(req):
            return "ACCESS GRANTED"

        response = fake_view(request)
        self.assertEqual(response, "ACCESS GRANTED")
