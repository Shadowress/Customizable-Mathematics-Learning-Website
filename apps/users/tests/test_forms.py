from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.users.forms import CustomSignupForm, ProfileUpdateForm

User = get_user_model()


class CustomSignupFormTest(TestCase):

    def test_valid_signup_form(self):
        form_data = {
            'username': 'testuser',
            'email': 'TestUser@example.com',
            'password1': 'strongpassword123',
            'password2': 'strongpassword123',
        }
        form = CustomSignupForm(data=form_data)
        self.assertTrue(form.is_valid())

        user = form.save()
        self.assertEqual(user.email, 'testuser@example.com')  # email should be lowercased
        self.assertTrue(user.check_password('strongpassword123'))

    def test_email_already_exists_with_password(self):
        User.objects.create_user(email='existing@example.com', password='pass123')

        form_data = {
            'username': 'anotheruser',
            'email': 'existing@example.com',
            'password1': 'anotherpass123',
            'password2': 'anotherpass123',
        }
        form = CustomSignupForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("An account with this email already exists.", form.errors['email'])

    def test_email_registered_with_google(self):
        user = User.objects.create(email='google@example.com')
        user.set_unusable_password()
        user.save()

        form_data = {
            'username': 'googleuser',
            'email': 'google@example.com',
            'password1': 'randompass456',
            'password2': 'randompass456',
        }
        form = CustomSignupForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("This email is registered with Google. Please log in using Google.", form.errors['email'])


class ProfileUpdateFormTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(email='profile@example.com', password='pass123', username='profileuser')

    def test_valid_profile_update_form(self):
        form_data = {
            'username': 'updatedname',
            'date_of_birth': '2000-01-01',
        }
        form = ProfileUpdateForm(instance=self.user, data=form_data)
        self.assertTrue(form.is_valid())

        updated_user = form.save()
        self.assertEqual(updated_user.username, 'updatedname')
        self.assertEqual(updated_user.date_of_birth, date(2000, 1, 1))
