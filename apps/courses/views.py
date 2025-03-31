from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, get_object_or_404

from apps.courses.models import Course
from apps.users.permissions import normal_user_required, content_manager_required


# Create your views here.
@user_passes_test(normal_user_required, login_url="homepage")
def course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    return render(request, "course.html", {"course": course})


@user_passes_test(content_manager_required, login_url="homepage")
def create_course(request):
    # if draft:
    form = ...
    return render(request, "create_course.html", {"form": form})
