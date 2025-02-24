from http.client import HTTPResponse

from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render

from apps.users.models import CustomUser


# Create your views here.
def normal_user_required(user) -> bool:
    return user.is_authenticated and user.role == CustomUser.NORMAL_USER


def content_manager_required(user) -> bool:
    return user.is_authenticated and user.role == CustomUser.CONTENT_MANAGER


@user_passes_test(normal_user_required)
def dashboard(request) -> HTTPResponse:
    return render(request, "dashboard.html", {})


@user_passes_test(content_manager_required)
def content_manager_dashboard(request) -> HTTPResponse:
    return render(request, "content_manager_dashboard.html", {})
