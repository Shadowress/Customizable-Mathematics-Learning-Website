from django.test import TestCase
from django.utils import timezone

from apps.users.models import CustomUser, EmailVerificationToken


class CustomUserModelTest(TestCase):

    def test_create_user_with_email(self):
        user = CustomUser.objects.create_user(email="user@example.com", password="testpass123")
        self.assertEqual(user.email, "user@example.com")
        self.assertTrue(user.check_password("testpass123"))
        self.assertEqual(user.username, "user")
        self.assertEqual(user.role, CustomUser.NORMAL_USER)

    def test_create_superuser(self):
        superuser = CustomUser.objects.create_superuser(email="admin@example.com", password="adminpass")
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)
        self.assertEqual(superuser.role, CustomUser.SUPERUSER)

    def test_str_returns_email(self):
        user = CustomUser.objects.create_user(email="user@example.com", password="test")
        self.assertEqual(str(user), "user@example.com")

    def test_user_role_methods(self):
        normal_user = CustomUser.objects.create_user(email="normal@example.com", password="123")
        manager = CustomUser.objects.create_user(email="manager@example.com", password="123",
                                                 role=CustomUser.CONTENT_MANAGER)
        superuser = CustomUser.objects.create_user(email="super@example.com", password="123", role=CustomUser.SUPERUSER)

        self.assertTrue(normal_user.is_normal_user())
        self.assertTrue(manager.is_content_manager())
        self.assertTrue(superuser.is_superuser_role())

    def test_default_fields(self):
        user = CustomUser.objects.create_user(email="test@example.com", password="test")
        self.assertFalse(user.is_verified)
        self.assertIsNone(user.date_of_birth)
        self.assertEqual(user.role, CustomUser.NORMAL_USER)
        self.assertIsNone(user.profile_picture.name)


class EmailVerificationTokenTest(TestCase):

    def test_create_token(self):
        user = CustomUser.objects.create_user(email="verify@example.com", password="123")
        token = EmailVerificationToken.objects.create(user=user, token="abc123")
        self.assertEqual(token.token, "abc123")
        self.assertEqual(str(token), f"Verification Token for {user.username}")
        self.assertLessEqual(token.created_at, timezone.now())
