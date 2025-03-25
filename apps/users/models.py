import os
from typing import Any

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.forms import EmailField


# Create your models here.
def user_profile_picture_path(instance, filename):
    """Save profile pictures inside 'media/profile_pictures/' without duplicate folders."""
    return os.path.join("profile_pictures", filename)


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields) -> Any:
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)

        if not extra_fields.get("username"):
            extra_fields["username"] = email.split("@")[0]

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields) -> Any:
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", CustomUser.SUPERUSER)

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    class Meta:
        app_label = "users"
        swappable = "AUTH_USER_MODEL"

    NORMAL_USER = "normal"
    CONTENT_MANAGER = "content_manager"
    SUPERUSER = "superuser"

    ROLE_CHOICES = [
        (NORMAL_USER, "Normal User"),
        (CONTENT_MANAGER, "Content Manager"),
        (SUPERUSER, "Superuser"),
    ]

    email = models.EmailField(unique=True)
    profile_picture = models.ImageField(upload_to=user_profile_picture_path, blank=True, null=True)
    username = models.CharField(max_length=150, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=NORMAL_USER)
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self) -> EmailField:
        return self.email

    def is_normal_user(self) -> bool:
        return self.role == self.NORMAL_USER

    def is_content_manager(self) -> bool:
        return self.role == self.CONTENT_MANAGER

    def is_superuser_role(self) -> bool:
        return self.role == self.SUPERUSER

    def save(self, *args, **kwargs) -> None:
        if self.pk:
            self.__class__.objects.filter(pk=self.pk).update(role=self.role)

        if not self.username:
            self.username = str(self.email).split("@")[0]

        super().save(*args, **kwargs)


class EmailVerificationToken(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    token = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Verification Token for {self.user.username}"
