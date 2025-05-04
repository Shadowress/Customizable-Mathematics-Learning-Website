from typing import Any

from django.http import HttpRequest
from django.shortcuts import redirect

INTERNAL_IPS = ["127.0.0.1"]  # todo add internal IPs


class RestrictAdminMiddleware:
    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        if request.path.startswith("/admin/") and not RestrictAdminMiddleware.is_internal(request):
            return redirect("/")
        return self.get_response(request)

    @staticmethod
    def is_internal(request: HttpRequest) -> bool:
        ip = request.META.get("REMOTE_ADDR", "")
        return ip.startswith("192.168.") or ip == "127.0.0.1"


class AdminLogoutOnExitMiddleware:
    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request) -> Any:
        response = self.get_response(request)

        if request.user.is_authenticated and request.user.is_superuser:
            if not request.path.startswith("/admin/"):
                request.session.flush()

        return response


class AdminRestrictionMiddleware:
    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)

        if request.path.startswith("/admin/") and not request.user.is_superuser:
            return redirect("/")

        return self.get_response(request)
