from typing import Any

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from .models import CustomUser


# Register your models here.
class CustomUserAdmin(UserAdmin):
    model = CustomUser

    list_display = ("email", "role", "is_active")
    search_fields = ("email",)
    list_filter = ("role", "is_active", "is_superuser")

    readonly_fields = ("email", "role", "date_of_birth", "username", "last_login", "date_joined")

    fieldsets = (
        (None, {"fields": ("email", "role")}),
        ("Personal Info", {"fields": ("username", "date_of_birth")}),
        ("Permissions", {"fields": ("is_active",)}),
        ("Important Dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        ("Basic Info", {"fields": ("email", "username", "password1", "password2")}),
    )

    def get_readonly_fields(self, request, obj=None) -> tuple[str, ...]:
        """Make all fields except 'is_active' read-only, unless it's a new user."""
        if not obj:
            return ()

        if not obj.is_superuser:
            return self.readonly_fields

        return self.readonly_fields + ("is_active",)

    # todo uncomment during production
    # def get_actions(self, request) -> dict | dict[Any, tuple[Any, Any, Any]]:
    #     """Remove delete action from the admin list page"""
    #     actions = super().get_actions(request)
    #     if "delete_selected" in actions:
    #         del actions["delete_selected"]
    #     return actions
    #
    # def get_model_perms(self, request) -> dict[str, Any]:
    #     """Remove the delete section in the user details page"""
    #     perms = super().get_model_perms(request)
    #     perms["delete"] = False  # This removes the delete button
    #     return perms
    #
    # def has_delete_permission(self, request, obj=None) -> bool:
    #     """Completely remove the delete button from user details page"""
    #     return False

    def add_view(self, request, form_url='', extra_context=None):
        """Change the title of the Add User page to 'Add Content Manager'."""
        extra_context = extra_context or {}
        extra_context['title'] = "Add Content Manager"
        return super().add_view(request, form_url, extra_context)


admin.site.unregister(Group)
admin.site.register(CustomUser, CustomUserAdmin)
