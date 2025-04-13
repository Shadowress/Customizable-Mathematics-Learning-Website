import json

from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import transaction
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.safestring import mark_safe

from apps.courses.models import Course, Content, Quiz, Section
from apps.users.permissions import normal_user_required, content_manager_required
from .forms import CourseForm, VideoContentFormSet, ImageContentFormSet, TextContentFormSet
from .forms import SectionFormSet, QuizFormSet


# Create your views here.
# --- Normal User ---
@user_passes_test(normal_user_required, login_url="homepage")
def course(request, slug):
    course = get_object_or_404(Course, slug=slug, status='published')
    return render(request, "normal_users/course.html", {"course": course})


# --- Content Manager ---
@user_passes_test(content_manager_required, login_url="homepage")
def create_or_edit_course(request, slug=None):
    if slug:
        course = get_object_or_404(Course, slug=slug, created_by=request.user)

    else:
        course = None

    section_prefix = "section"
    text_content_prefix = "text_content"
    image_content_prefix = "image_content"
    video_content_prefix = "video_content"
    quiz_prefix = "quiz"

    if request.method == "POST":
        with transaction.atomic():
            course_form = CourseForm(request.POST, instance=course)
            section_formset = SectionFormSet(request.POST, instance=course, prefix=section_prefix)
            text_content_formset = TextContentFormSet(
                request.POST,
                queryset=Content.objects.filter(section__course=course),
                prefix=text_content_prefix
            )
            image_content_formset = ImageContentFormSet(
                request.POST,
                queryset=Content.objects.filter(section__course=course),
                prefix=image_content_prefix
            )
            video_content_formset = VideoContentFormSet(
                request.POST,
                queryset=Content.objects.filter(section__course=course),
                prefix=video_content_prefix
            )
            quiz_formset = QuizFormSet(
                request.POST,
                queryset=Quiz.objects.filter(section__course=course),
                prefix=quiz_prefix
            )

            if all([
                course_form.is_valid(),
                section_formset.is_valid(),
                text_content_formset.is_valid(),
                image_content_formset.is_valid(),
                video_content_formset.is_valid(),
                quiz_formset.is_valid()
            ]):
                course = course_form.save(commit=False)

                action = request.POST.get("action")
                if action == "publish":
                    course.status = Course.PUBLISHED
                else:
                    course.status = Course.DRAFT

                course.created_by = request.user
                course.save()

                section_lookup = {}

                for form in section_formset.forms:
                    section_id = form.cleaned_data.get("id")
                    marked_for_deletion = form.cleaned_data.get("DELETE", False)

                    if not section_id:
                        if marked_for_deletion:
                            continue

                        section = Section()

                    else:
                        try:
                            section = Section.objects.get(pk=section_id.pk)
                        except Section.DoesNotExist:
                            raise ValidationError(f"Section with ID {section_id} does not exist.")

                        if marked_for_deletion:
                            section.delete()
                            continue

                    section.course = course
                    section.title = form.cleaned_data.get("title")
                    section.order = form.cleaned_data.get("order")
                    section.save()

                    if section.order is not None:
                        section_lookup[section.order] = section

                _save_content_and_quiz_formset(text_content_formset, section_lookup, content_type="text")
                _save_content_and_quiz_formset(image_content_formset, section_lookup, content_type="image")
                _save_content_and_quiz_formset(video_content_formset, section_lookup, content_type="video")
                _save_content_and_quiz_formset(quiz_formset, section_lookup, content_type="quiz")

                return redirect("content_manager_dashboard")

    else:
        course_form = CourseForm(instance=course) if course else CourseForm()
        section_formset = SectionFormSet(prefix=section_prefix)
        text_content_formset = TextContentFormSet(prefix=text_content_prefix)
        image_content_formset = ImageContentFormSet(prefix=image_content_prefix)
        video_content_formset = VideoContentFormSet(prefix=video_content_prefix)
        quiz_formset = QuizFormSet(prefix=quiz_prefix)

        serialized_sections = _serialize_json_safe(
            _serialize_section_formset(
                SectionFormSet(
                    instance=course, prefix=section_prefix
                )
            )
        ) if course else []

        section_qs = Section.objects.filter(course=course).order_by("order") if course else []

        serialized_text_contents = []
        serialized_image_contents = []
        serialized_video_contents = []
        serialized_quizzes = []

        for section in section_qs:
            # TEXT
            text_formset = TextContentFormSet(
                instance=section,
                prefix=text_content_prefix,
                queryset=Content.objects.filter(section=section, content_type=Content.TEXT))

            for form in text_formset:
                form.fields['section_order'].initial = section.order

            serialized_text_contents.extend(_serialize_text_content_formset(text_formset))

            # IMAGE
            image_formset = ImageContentFormSet(
                instance=section,
                prefix=image_content_prefix,
                queryset=Content.objects.filter(section=section, content_type=Content.IMAGE))

            for form in image_formset:
                form.fields['section_order'].initial = section.order

            serialized_image_contents.extend(_serialize_image_content_formset(image_formset))

            # VIDEO
            video_formset = VideoContentFormSet(
                instance=section,
                prefix=video_content_prefix,
                queryset=Content.objects.filter(section=section, content_type=Content.VIDEO))

            for form in video_formset:
                form.fields['section_order'].initial = section.order

            serialized_video_contents.extend(_serialize_video_content_formset(video_formset))

            # QUIZ
            quiz_formset_data = QuizFormSet(
                instance=section,
                prefix=quiz_prefix,
                queryset=Quiz.objects.filter(section=section))

            for form in quiz_formset_data:
                form.fields['section_order'].initial = section.order

            serialized_quizzes.extend(_serialize_quiz_formset(quiz_formset_data))

        serialized_text_contents = _serialize_json_safe(serialized_text_contents)
        serialized_image_contents = _serialize_json_safe(serialized_image_contents)
        serialized_video_contents = _serialize_json_safe(serialized_video_contents)
        serialized_quizzes = _serialize_json_safe(serialized_quizzes)

    return render(
        request,
        "content_managers/create_or_edit_course.html",
        {
            "course_form": course_form,
            "section_formset": section_formset,
            "text_content_formset": text_content_formset,
            "image_content_formset": image_content_formset,
            "video_content_formset": video_content_formset,
            "quiz_formset": quiz_formset,

            # Serialized JSON for course edit
            "existing_sections": serialized_sections,
            "existing_text_contents": serialized_text_contents,
            "existing_image_contents": serialized_image_contents,
            "existing_video_contents": serialized_video_contents,
            "existing_quizzes": serialized_quizzes,
        }
    )


# --- Private Methods ---
def _save_content_and_quiz_formset(formset, section_lookup, content_type=None):
    for form in formset:
        cleaned_data = form.cleaned_data
        instance_id = cleaned_data.get("id")
        marked_for_deletion = cleaned_data.get("DELETE", False)

        if not instance_id:
            if marked_for_deletion:
                continue

            instance = form._meta.model()

        else:
            try:
                instance = form._meta.model.objects.get(pk=instance_id.pk)
            except ObjectDoesNotExist:
                continue

            if marked_for_deletion:
                instance.delete()
                continue

        section_order = form.cleaned_data.get('section_order')
        if section_order is not None:
            section = section_lookup.get(section_order)

            if section is None:
                continue

            instance.section = section

        if content_type == "text":
            instance.content_type = Content.TEXT
            instance.text_content = cleaned_data.get("text_content")

        elif content_type == "image":
            instance.content_type = Content.IMAGE
            instance.image = cleaned_data.get("image")
            instance.alt_text = cleaned_data.get("alt_text")

        elif content_type == "video":
            instance.content_type = Content.VIDEO
            instance.video_url = cleaned_data.get("video_url")
            instance.video_transcription = cleaned_data.get("video_transcription")

        elif content_type == "quiz":
            instance.question = cleaned_data.get("question")
            instance.correct_answer = cleaned_data.get("correct_answer")

        instance.order = form.cleaned_data.get('order')
        instance.save()


def _serialize_json_safe(data):
    return mark_safe(json.dumps(data))


def _serialize_section_formset(section_formset):
    return [
        {
            "id": form.instance.id,
            "title": form.instance.title,
            "order": form.instance.order,
        }
        for form in section_formset.forms
        if form.instance.pk
    ]


def _serialize_text_content_formset(text_content_formset):
    return [
        {
            "id": form.instance.id,
            "content_type": form.instance.content_type,
            "text_content": form.instance.text_content,
            "order": form.instance.order,
            "section_order": form.fields["section_order"].initial,
        }
        for form in text_content_formset.forms
        if form.instance.pk
    ]


def _serialize_image_content_formset(image_content_formset):
    return [
        {
            "id": form.instance.id,
            "content_type": form.instance.content_type,
            "image": form.instance.image.url if form.instance.image else None,
            "alt_text": form.instance.alt_text,
            "order": form.instance.order,
            "section_order": form.fields["section_order"].initial,
        }
        for form in image_content_formset.forms
        if form.instance.pk
    ]


def _serialize_video_content_formset(video_content_formset):
    return [
        {
            "id": form.instance.id,
            "content_type": form.instance.content_type,
            "video_url": form.instance.video_url,
            "video_transcription": form.instance.video_transcription,
            "order": form.instance.order,
            "section_order": form.fields["section_order"].initial,
        }
        for form in video_content_formset.forms
        if form.instance.pk
    ]


def _serialize_quiz_formset(quiz_formset):
    return [
        {
            "id": form.instance.id,
            "question": form.instance.question,
            "correct_answer": form.instance.correct_answer,
            "order": form.instance.order,
            "section_order": form.fields["section_order"].initial,
        }
        for form in quiz_formset.forms
        if form.instance.pk
    ]
