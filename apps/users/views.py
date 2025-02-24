from http.client import HTTPResponse

from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import render, redirect


# Create your views here.
def home(request) -> HTTPResponse:
    if not request.user.is_authenticated:
        return render(request, "home.html", {})

    if request.user.is_superuser:
        return redirect("admin:index")

    return redirect("dashboard")


def login_view(request) -> HTTPResponse:
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = AuthenticationForm(request.POST)
        if form.is_valid():
            return redirect("dashboard")
    else:
        form = AuthenticationForm()

    return render(request, "login.html", {"form": form})


def sign_up_view(request) -> HTTPResponse:
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("dashboard")
    else:
        form = UserCreationForm()

    return render(request, "register.html", {"form": form})
