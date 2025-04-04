from django.contrib.auth.decorators import user_passes_test
from django.db import transaction
from django.shortcuts import get_object_or_404, render, redirect

from apps.courses.models import Course
from apps.users.permissions import normal_user_required, content_manager_required
from .forms import CourseForm, VideoContentInlineFormSet, ImageContentInlineFormSet, TextContentInlineFormSet
from .forms import SectionFormSet, QuizFormSet


# Create your views here.
@user_passes_test(normal_user_required, login_url="homepage")
def course(request, course_id):
    course = Course.objects.filter(status='published')
    return render(request, "normal_users/course.html", {"course": course})


@user_passes_test(content_manager_required, login_url="homepage")
def create_course(request):
    if request.method == "POST":
        course_form = CourseForm(request.POST)

        if course_form.is_valid():
            with transaction.atomic():
                course = course_form.save(commit=False)  # Do not save to DB yet
                course.created_by = request.user  # Assign course creator
                course.save()  # Save course first (so it gets an ID)

                # Save sections
                section_formset = SectionFormSet(request.POST, instance=course)
                if section_formset.is_valid():
                    sections = section_formset.save(commit=False)  # Delay save
                    for section in sections:
                        section.course = course  # Assign the course
                        section.save()  # Now save the section

                        # Handle Text Content
                        text_content_formset = TextContentInlineFormSet(request.POST, instance=section)
                        if text_content_formset.is_valid():
                            text_contents = text_content_formset.save(commit=False)
                            for content in text_contents:
                                content.section = section
                                content.save()

                        # Handle Image Content
                        image_content_formset = ImageContentInlineFormSet(request.POST, instance=section)
                        if image_content_formset.is_valid():
                            image_contents = image_content_formset.save(commit=False)
                            for content in image_contents:
                                content.section = section
                                content.save()

                        # Handle Video Content
                        video_content_formset = VideoContentInlineFormSet(request.POST, instance=section)
                        if video_content_formset.is_valid():
                            video_contents = video_content_formset.save(commit=False)
                            for content in video_contents:
                                content.section = section
                                content.save()

                        # Handle Quizzes
                        quiz_formset = QuizFormSet(request.POST, instance=section)
                        if quiz_formset.is_valid():
                            quizzes = quiz_formset.save(commit=False)
                            for quiz in quizzes:
                                quiz.section = section  # Link quiz to section
                                quiz.save()

                    return redirect("homepage")

    else:
        course_form = CourseForm()
        section_formset = SectionFormSet()
        text_content_formset = TextContentInlineFormSet()
        image_content_formset = ImageContentInlineFormSet()
        video_content_formset = VideoContentInlineFormSet()
        quiz_formset = QuizFormSet()

    return render(
        request,
        "content_managers/create_course.html",
        {
            "course_form": course_form,
            "section_formset": section_formset,
            "text_content_formset": text_content_formset,
            "image_content_formset": image_content_formset,
            "video_content_formset": video_content_formset,
            "quiz_formset": quiz_formset
        }
    )


@user_passes_test(content_manager_required, login_url="homepage")
def edit_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    # Add logic for editing the course (e.g., form handling)
    return render(request, "content_managers/edit_course.html", {"course": course})
