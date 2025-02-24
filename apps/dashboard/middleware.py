from http.client import HTTPResponse

from django.shortcuts import redirect


class AdminRestrictionMiddleware:
    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request) -> HTTPResponse:
        if not request.user.is_authenticated:
            return self.get_response(request)

        if request.path.startswith("/admin/") and not request.user.is_superuser:
            return redirect("/")

        return self.get_response(request)
