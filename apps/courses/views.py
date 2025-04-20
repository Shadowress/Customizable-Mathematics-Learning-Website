import json
import os
import tempfile

import whisper
import yt_dlp
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_POST

from apps.courses.models import Course, Content, Quiz, Section, Answer, ScheduledCourse
from apps.users.permissions import normal_user_required, content_manager_required
from .forms import CourseForm, VideoContentFormSet, ImageContentFormSet, TextContentFormSet
from .forms import SectionFormSet, QuizFormSet


# Create your views here.
# --- Normal User ---
@user_passes_test(normal_user_required, login_url="homepage")
def course(request, slug):
    course_qs = get_object_or_404(Course, slug=slug)
    user = request.user
    sections_qs = Section.objects.filter(course=course_qs).order_by('order')

    is_saved = False
    if request.user.is_authenticated:
        is_saved = course_qs in request.user.saved_courses.all()

    scheduled_course = ScheduledCourse.objects.filter(
        user=request.user,
        course=course_qs,
        scheduled_time__gt=now()
    ).order_by('scheduled_time').first()

    is_completed = course_qs in user.completed_courses.all()

    course = {
        "id": course_qs.id,
        "title": course_qs.title,
        "description": course_qs.description,
        "difficulty": course_qs.difficulty,
        "estimated_completion_time": course_qs.estimated_completion_time,
        "is_saved": is_saved,
        "scheduled_time": scheduled_course.scheduled_time if scheduled_course else None,
        "is_completed": is_completed,
    }

    sections = []
    video_transcriptions = {}

    for section in sections_qs:
        contents = []
        raw_contents = Content.objects.filter(section=section).order_by("order")

        for content in raw_contents:
            if content.content_type == "text":
                contents.append({
                    "id": content.id,
                    "type": "text",
                    "text_content": content.text_content,
                    "order": content.order,
                })
            elif content.content_type == "image":
                contents.append({
                    "id": content.id,
                    "type": "image",
                    "image": content.image.url if content.image else "",
                    "alt_text": content.alt_text,
                    "order": content.order,
                })
            elif content.content_type == "video":
                contents.append({
                    "id": content.id,
                    "type": "video",
                    "video_url": content.video_url,
                    "order": content.order,
                })

                if content.video_transcription:
                    video_transcriptions[content.id] = content.video_transcription

        quiz_data = []
        quizzes = Quiz.objects.filter(section=section).order_by("order")
        for quiz in quizzes:
            try:
                Answer.objects.get(user=request.user, quiz=quiz)
                show_answer = True
                placeholder = quiz.correct_answer
            except Answer.DoesNotExist:
                show_answer = False
                placeholder = "".join(
                    "_" if c not in [" ", "/", ",", ".", "\"", "'", ":"] else c for c in quiz.correct_answer or "")

            quiz_data.append({
                "id": quiz.id,
                "question": quiz.question,
                "placeholder": placeholder,
                "order": quiz.order,
                "show_answer": show_answer
            })

        sections.append({
            "title": section.title,
            "order": section.order,
            "contents": contents,
            "quizzes": quiz_data,
        })

    return render(
        request,
        "normal_users/course.html",
        {
            "normal_user_header_included": True,
            "course": course,
            "sections": sections,
            "video_transcriptions": video_transcriptions
        }
    )


@require_POST
@user_passes_test(normal_user_required, login_url="homepage")
def submit_quiz_answer(request):
    # Parse the JSON body
    try:
        data = json.loads(request.body)
        quiz_id = data.get("quiz_id")
        user_answer = data.get("answer", "").strip().lower()
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON format."})

    user = request.user

    if not quiz_id:
        return JsonResponse({"success": False, "message": "Missing quiz ID."})

    try:
        quiz = Quiz.objects.get(id=quiz_id)
    except Quiz.DoesNotExist:
        return JsonResponse({"success": False, "message": "Invalid quiz."})

    correct_answer = (quiz.correct_answer or "").strip()
    is_correct = user_answer == correct_answer.lower()

    if is_correct:
        Answer.objects.get_or_create(user=user, quiz=quiz)

        # If the user has answered all quizzes in the course, mark it as completed
        course_quizzes = Quiz.objects.filter(section__course=quiz.section.course)
        answered_quizzes = Answer.objects.filter(user=user, quiz__in=course_quizzes)

        if answered_quizzes.count() == course_quizzes.count():
            user.completed_courses.add(quiz.section.course)

            ScheduledCourse.objects.filter(
                user=user,
                course=quiz.section.course,
                scheduled_time__gt=now()
            ).delete()

        return JsonResponse({
            "success": True,
            "is_correct": True,
            "message": "Correct!",
            "quiz_id": quiz.id,
            "correct_answer": correct_answer,
        })

    else:
        return JsonResponse({
            "success": True,
            "is_correct": False,
            "message": "Incorrect answer.",
            "quiz_id": quiz.id,
        })



@user_passes_test(normal_user_required, login_url="homepage")
def toggle_save_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    user = request.user

    if course in user.saved_courses.all():
        user.saved_courses.remove(course)
    else:
        user.saved_courses.add(course)

    return redirect('course', slug=course.slug)


from django.utils.timezone import make_aware, now
from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test


@user_passes_test(normal_user_required, login_url="homepage")
def schedule_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.method == "POST":
        action = request.POST.get("action")
        scheduled_time_str = request.POST.get("scheduled_time")
        existing_schedule = ScheduledCourse.objects.filter(user=request.user, course=course).first()

        # Validate time input for scheduling and rescheduling
        def parse_scheduled_time():
            if not scheduled_time_str:
                messages.error(request, "Scheduled time is required.")
                return None
            try:
                scheduled_time = make_aware(datetime.strptime(scheduled_time_str, "%Y-%m-%dT%H:%M"))
            except ValueError:
                messages.error(request, "Invalid date/time format.")
                return None
            if scheduled_time < now() + timedelta(minutes=30):
                messages.error(request, "Please select a time at least 30 minutes from now.")
                return None
            return scheduled_time

        if action == "schedule":
            if existing_schedule:
                messages.warning(request, "This course is already scheduled.")
            else:
                scheduled_time = parse_scheduled_time()
                if scheduled_time:
                    ScheduledCourse.objects.create(
                        user=request.user,
                        course=course,
                        scheduled_time=scheduled_time
                    )
                    messages.success(request, "✅ Course successfully scheduled!")

        elif action == "reschedule":
            if not existing_schedule:
                messages.error(request, "No existing schedule found to reschedule.")
            else:
                scheduled_time = parse_scheduled_time()
                if scheduled_time:
                    existing_schedule.scheduled_time = scheduled_time
                    existing_schedule.save()
                    messages.success(request, "✅ Course successfully rescheduled!")

        elif action == "unschedule":
            if not existing_schedule:
                messages.warning(request, "No schedule exists for this course.")
            else:
                existing_schedule.delete()
                messages.success(request, "⛔ Course unscheduled.")

        else:
            messages.error(request, "Invalid action.")

    return redirect('course', slug=course.slug)


# --- Content Manager ---
@user_passes_test(content_manager_required, login_url="homepage")
def create_or_edit_course(request, slug=None):
    if slug:
        course = get_object_or_404(Course, slug=slug, created_by=request.user)
        if course.status == "draft":
            mode = "edit_draft"
        else:
            mode = "edit_published"

    else:
        course = None
        mode = "create"

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
                request.FILES,
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

            FIELD_WHITELISTS = {
                "section": ["id", "title", "order"],
                "text": ["id", "content_type", "text_content", "order", "section_order"],
                "image": ["id", "content_type", "image", "alt_text", "order", "section_order"],
                "video": ["id", "content_type", "video_url", "video_transcription", "order", "section_order"],
                "quiz": ["id", "question", "correct_answer", "order", "section_order"],
            }

            serialized_sections = [
                _clean_for_json(form.cleaned_data if form.is_valid() else form.data, FIELD_WHITELISTS["section"])
                for form in section_formset.forms
                if _form_has_non_empty_fields(form, FIELD_WHITELISTS["section"])
            ]

            serialized_text_contents = [
                _clean_for_json(form.cleaned_data if form.is_valid() else form.data, FIELD_WHITELISTS["text"])
                for form in text_content_formset.forms
                if _form_has_non_empty_fields(form, FIELD_WHITELISTS["text"])
            ]

            serialized_image_contents = [
                _clean_for_json(form.cleaned_data if form.is_valid() else form.data, FIELD_WHITELISTS["image"])
                for form in image_content_formset.forms
                if _form_has_non_empty_fields(form, FIELD_WHITELISTS["image"])
            ]

            serialized_video_contents = [
                _clean_for_json(form.cleaned_data if form.is_valid() else form.data, FIELD_WHITELISTS["video"])
                for form in video_content_formset.forms
                if _form_has_non_empty_fields(form, FIELD_WHITELISTS["video"])
            ]

            serialized_quizzes = [
                _clean_for_json(form.cleaned_data if form.is_valid() else form.data, FIELD_WHITELISTS["quiz"])
                for form in quiz_formset.forms
                if _form_has_non_empty_fields(form, FIELD_WHITELISTS["quiz"])
            ]

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

                elif action == "save_draft":
                    course.status = Course.DRAFT
                    ScheduledCourse.objects.filter(course=course).delete()

                elif action == "delete_course":
                    course.delete()
                    return redirect("content_manager_dashboard")

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

        serialized_sections = _serialize_section_formset(
            SectionFormSet(
                instance=course, prefix=section_prefix
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

    serialized_sections = _serialize_json_safe(serialized_sections)
    serialized_text_contents = _serialize_json_safe(serialized_text_contents)
    serialized_image_contents = _serialize_json_safe(serialized_image_contents)
    serialized_video_contents = _serialize_json_safe(serialized_video_contents)
    serialized_quizzes = _serialize_json_safe(serialized_quizzes)

    print(serialized_image_contents)

    section_formset = SectionFormSet(prefix=section_prefix)
    text_content_formset = TextContentFormSet(prefix=text_content_prefix)
    image_content_formset = ImageContentFormSet(prefix=image_content_prefix)
    video_content_formset = VideoContentFormSet(prefix=video_content_prefix)
    quiz_formset = QuizFormSet(prefix=quiz_prefix)

    return render(
        request,
        "content_managers/create_or_edit_course.html",
        {
            "mode": mode,

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


@require_POST
def transcribe_video(request):
    video_url = request.POST.get('video_url')

    if not video_url:
        return JsonResponse({'status': 'error', 'message': 'Missing video URL'}, status=400)

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            audio_path = os.path.join(temp_dir, "audio.wav")

            # 1. Download and extract audio
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(temp_dir, 'audio.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                    'preferredquality': '192',
                }],
                'quiet': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])

            # Find the audio file
            for file in os.listdir(temp_dir):
                if file.endswith(".wav"):
                    audio_path = os.path.join(temp_dir, file)
                    break

            # 2. Transcribe audio using whisper
            model = whisper.load_model("base")  # Or "tiny" for faster, lower accuracy
            result = model.transcribe(audio_path)

            transcription = result.get("text", "")

            return JsonResponse({
                'status': 'success',
                'transcription': transcription,
                'video_url': video_url,
            })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


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


def _clean_for_json(data, allowed_fields=None):
    """Return a cleaned dict with only allowed fields and convert values to JSON-serializable types."""
    if not isinstance(data, dict):
        return {}

    cleaned = {}
    for key in allowed_fields or data.keys():
        value = data.get(key)

        # Handle model instances (e.g. Section or Course)
        if hasattr(value, 'pk'):
            cleaned[key] = value.pk

        # Handle UploadedFile/FileField/ImageField
        elif hasattr(value, 'url'):
            cleaned[key] = value.url

        # Handle everything else (assume JSON-serializable)
        else:
            cleaned[key] = value

    return cleaned


def _form_has_non_empty_fields(form, whitelist):
    """Returns True if the form has at least one non-empty whitelisted field."""
    data = form.cleaned_data if form.is_valid() else form.data
    return any(data.get(field) not in [None, '', False] for field in whitelist)


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
