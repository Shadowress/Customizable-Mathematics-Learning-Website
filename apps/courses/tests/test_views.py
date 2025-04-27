import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.utils.timezone import now

from apps.courses.forms import TextContentFormSet, ImageContentFormSet, VideoContentFormSet, QuizFormSet, SectionFormSet
from apps.courses.models import Course, Section, Quiz, Content, ScheduledCourse
from apps.courses.views import (
    _save_content_and_quiz_formset,
    _clean_for_json,
    _form_has_non_empty_fields,
    _serialize_section_formset,
    _serialize_text_content_formset,
    _serialize_image_content_formset,
    _serialize_video_content_formset,
    _serialize_quiz_formset,
)

User = get_user_model()


class NormalUserViewTests(TestCase):
    def setUp(self):
        # Create a normal user
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='password123',
            email='testuser@example.com',
            role='normal',
            is_verified=True
        )
        self.client.login(email='testuser@example.com', password='password123')

        # Create a sample course and section for testing
        self.course = Course.objects.create(
            title="Test Course",
            description="Test description",
            difficulty="junior",
            estimated_completion_time=30
        )
        self.section = Section.objects.create(
            title="Intro Section",
            course=self.course,
            order=1
        )
        # Create a quiz for the section
        self.quiz = Quiz.objects.create(
            question="What is 2 + 2?",
            correct_answer="4",
            section=self.section,
            order=0
        )
        # Create content for the section (e.g., text, image)
        self.content = Content.objects.create(
            content_type="text",
            text_content="Sample text content",
            section=self.section,
            order=0
        )

    def test_course_view(self):
        # Test the course detail view for a normal user
        response = self.client.get(reverse('course', kwargs={'slug': self.course.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.course.title)
        self.assertContains(response, self.section.title)

    def test_submit_quiz_answer_correct(self):
        # Test submitting a correct quiz answer
        response = self.client.post(reverse('submit_quiz_answer'), data={
            'quiz_id': self.quiz.id,
            'answer': '4'
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response_data = response.content.decode('utf-8')
        self.assertJSONEqual(response_data, {
            "success": True,
            "is_correct": True,
            "message": "Correct!",
            "quiz_id": self.quiz.id,
            "correct_answer": "4",
            "reload": True
        })

    def test_submit_quiz_answer_incorrect(self):
        # Test submitting an incorrect quiz answer
        response = self.client.post(reverse('submit_quiz_answer'), data={
            'quiz_id': self.quiz.id,
            'answer': '5'
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response_data = response.content.decode('utf-8')
        self.assertJSONEqual(response_data, {
            "success": True,
            "is_correct": False,
            "message": "Incorrect answer.",
            "quiz_id": self.quiz.id,
            "reload": False
        })

    def test_toggle_save_course(self):
        # Test toggling the saved courses
        response = self.client.get(reverse('toggle_save_course', kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 302)  # Redirect
        # Check that the course is now saved
        self.assertTrue(self.user.saved_courses.filter(id=self.course.id).exists())

        # Toggle again to unsave
        response = self.client.get(reverse('toggle_save_course', kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 302)  # Redirect
        # Check that the course is now unsaved
        self.assertFalse(self.user.saved_courses.filter(id=self.course.id).exists())

    def test_schedule_course(self):
        # Test scheduling a course
        scheduled_time = now() + timedelta(hours=1)
        response = self.client.post(reverse('schedule_course', kwargs={'course_id': self.course.id}), data={
            'action': 'schedule',
            'scheduled_time': scheduled_time.strftime('%Y-%m-%dT%H:%M')
        })
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertTrue(ScheduledCourse.objects.filter(user=self.user, course=self.course).exists())

    def test_reschedule_course(self):
        # Test rescheduling a course
        scheduled_time = now() + timedelta(hours=1)
        ScheduledCourse.objects.create(
            user=self.user,
            course=self.course,
            scheduled_time=scheduled_time - timedelta(days=1)
        )
        new_scheduled_time = now() + timedelta(hours=2)
        response = self.client.post(reverse('schedule_course', kwargs={'course_id': self.course.id}), data={
            'action': 'reschedule',
            'scheduled_time': new_scheduled_time.strftime('%Y-%m-%dT%H:%M')
        })

        self.assertEqual(response.status_code, 302)
        updated_schedule = ScheduledCourse.objects.filter(user=self.user, course=self.course).first()
        updated_scheduled_time_truncated = updated_schedule.scheduled_time.replace(second=0, microsecond=0)
        new_scheduled_time_truncated = new_scheduled_time.replace(second=0, microsecond=0)
        self.assertEqual(updated_scheduled_time_truncated, new_scheduled_time_truncated,
                         f"Expected {updated_scheduled_time_truncated} to be equal to {new_scheduled_time_truncated}")

    def test_unschedule_course(self):
        # Test unscheduling a course
        scheduled_time = now() + timedelta(hours=1)
        scheduled_course = ScheduledCourse.objects.create(
            user=self.user,
            course=self.course,
            scheduled_time=scheduled_time
        )
        response = self.client.post(reverse('schedule_course', kwargs={'course_id': self.course.id}), data={
            'action': 'unschedule',
            'scheduled_time': ''
        })
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertFalse(ScheduledCourse.objects.filter(id=scheduled_course.id).exists())


class ContentManagerViewsTest(TestCase):
    def setUp(self):
        self.client = Client()

        # Create a content_manager user
        self.content_manager = User.objects.create_user(
            username="manager", email="manager@example.com", password="password", role="content_manager"
        )

        self.client.login(email="manager@example.com", password="password")

        # Create a sample course
        self.course = Course.objects.create(
            title="Sample Course",
            slug="sample-course",
            description="Sample description.",
            difficulty=Course.JUNIOR,
            estimated_completion_time=45,
            created_by=self.content_manager,
            status=Course.DRAFT,
        )

    def test_create_course_get(self):
        url = reverse('create_course')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "content_managers/create_or_edit_course.html")

    def test_edit_course_get(self):
        url = reverse('edit_course', kwargs={'slug': self.course.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "content_managers/create_or_edit_course.html")
        self.assertContains(response, self.course.title)

    def test_publish_course_post(self):
        url = reverse('edit_course', kwargs={'slug': self.course.slug})
        response = self.client.post(url, {
            'title': 'Updated Course Title',
            'description': 'Updated description.',
            'difficulty': Course.JUNIOR,
            'estimated_completion_time': 45,
            'action': 'publish',
            'section-TOTAL_FORMS': '1',
            'section-INITIAL_FORMS': '0',
            'section-0-title': 'Section 1',
            'section-0-order': '1',
            'section-0-description': 'Section description',
            'text_content-TOTAL_FORMS': '0',
            'text_content-INITIAL_FORMS': '0',
            'image_content-TOTAL_FORMS': '0',
            'image_content-INITIAL_FORMS': '0',
            'video_content-TOTAL_FORMS': '0',
            'video_content-INITIAL_FORMS': '0',
            'quiz-TOTAL_FORMS': '0',
            'quiz-INITIAL_FORMS': '0',
        })

        self.course.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.course.status, Course.PUBLISHED)

    def test_delete_course_post(self):
        url = reverse('edit_course', kwargs={'slug': self.course.slug})
        response = self.client.post(url, {
            'action': 'delete_course',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Course.objects.filter(id=self.course.id).exists())

    def test_transcribe_video_missing_url(self):
        url = reverse('transcribe_video')
        response = self.client.post(url, {})  # No video_url
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'status': 'error', 'message': 'Missing video URL'})

    def test_transcribe_video_invalid_url(self):
        self.client.login(username='content_manager_user', password='password123')
        url = reverse('transcribe_video')
        response = self.client.post(url, {'video_url': 'invalid_url'})
        self.assertEqual(response.status_code, 500)

        data = json.loads(response.content)
        self.assertEqual(data['status'], 'error')
        self.assertIn('message', data)


class SaveContentAndQuizFormsetTests(TestCase):
    def test_save_content_and_quiz_formset_creates_new_instance(self):
        course = Course.objects.create(
            title="Dummy Course",
            description="This is a dummy course for testing purposes.",
            difficulty=Course.JUNIOR,
            estimated_completion_time=45
        )
        section = Section.objects.create(course=course, title="Section 1", order=0)
        section_lookup = {0: section}
        formset_data = {
            'text-content-TOTAL_FORMS': 1,
            'text-content-INITIAL_FORMS': 0,
            'text-content-MIN_NUM_FORMS': 1,
            'text-content-MAX_NUM_FORMS': 1000,
            'text-content-0-content_type': 'text',
            'text-content-0-text_content': 'Sample Text',
            'text-content-0-order': 0,
            'text-content-0-section_order': 0,
        }
        formset = TextContentFormSet(data=formset_data, prefix="text-content")
        if formset.is_valid():
            _save_content_and_quiz_formset(formset, section_lookup, content_type="text")
        self.assertTrue(Content.objects.filter(text_content="Sample Text", section=section).exists())

    def test_clean_for_json_filters_allowed_fields(self):
        input_data = {
            'id': 1,
            'name': 'Test',
            'extra_field': 'Should be removed',
        }
        allowed = ['id', 'name']
        cleaned = _clean_for_json(input_data, allowed_fields=allowed)

        self.assertEqual(cleaned, {'id': 1, 'name': 'Test'})

    def test_form_has_non_empty_fields_returns_true_if_field_is_filled(self):
        form = TextContentFormSet(data={'name': 'Alice', 'age': ''})
        self.assertTrue(_form_has_non_empty_fields(form, ['name', 'age']))

    def test_form_has_non_empty_fields_returns_false_if_all_empty(self):
        form = TextContentFormSet(data={'name': '', 'age': ''})
        self.assertFalse(_form_has_non_empty_fields(form, ['name', 'age']))

    def test_serialize_section_formset_returns_expected_data(self):
        course = Course.objects.create(
            title="Dummy Course",
            description="This is a dummy course for testing purposes.",
            difficulty=Course.JUNIOR,
            estimated_completion_time=45
        )
        section = Section.objects.create(course=course, title="Test Section", order=1)
        formset = SectionFormSet(instance=course, queryset=Section.objects.filter(course=course))
        serialized = _serialize_section_formset(formset)
        self.assertEqual(serialized, [{
            "id": section.id,
            "title": "Test Section",
            "order": 1,
        }])

    def test_serialize_text_content_formset_handles_text_content(self):
        course = Course.objects.create(
            title="Dummy Course",
            description="This is a dummy course for testing purposes.",
            difficulty=Course.JUNIOR,
            estimated_completion_time=45
        )
        section = Section.objects.create(course=course, title="Text Section", order=1)
        Content.objects.create(section=section, content_type=Content.TEXT, text_content="Sample", order=1)
        formset = TextContentFormSet(instance=section, queryset=Content.objects.filter(section=section))
        serialized = _serialize_text_content_formset(formset)
        self.assertEqual(serialized[0]['text_content'], "Sample")

    def test_serialize_image_content_formset_handles_image_content(self):
        course = Course.objects.create(
            title="Dummy Course",
            description="This is a dummy course for testing purposes.",
            difficulty=Course.JUNIOR,
            estimated_completion_time=45
        )
        section = Section.objects.create(course=course, title="Image Section", order=2)
        Content.objects.create(section=section, content_type=Content.IMAGE, order=1, image=None)
        formset = ImageContentFormSet(instance=section, queryset=Content.objects.filter(section=section))
        serialized = _serialize_image_content_formset(formset)
        self.assertIsNone(serialized[0]['image'])

    def test_serialize_video_content_formset_handles_video_content(self):
        course = Course.objects.create(
            title="Dummy Course",
            description="This is a dummy course for testing purposes.",
            difficulty=Course.JUNIOR,
            estimated_completion_time=45
        )
        section = Section.objects.create(course=course, title="Video Section", order=3)
        Content.objects.create(section=section, content_type=Content.VIDEO, video_url="http://example.com", order=1)
        formset = VideoContentFormSet(instance=section, queryset=Content.objects.filter(section=section))
        serialized = _serialize_video_content_formset(formset)
        self.assertEqual(serialized[0]['video_url'], "http://example.com")

    def test_serialize_quiz_formset_handles_quiz_content(self):
        course = Course.objects.create(
            title="Dummy Course",
            description="This is a dummy course for testing purposes.",
            difficulty=Course.JUNIOR,
            estimated_completion_time=45
        )
        section = Section.objects.create(course=course, title="Quiz Section", order=4)
        Quiz.objects.create(section=section, question="What is 2+2?", correct_answer="4", order=1)
        formset = QuizFormSet(instance=section, queryset=Quiz.objects.filter(section=section))
        serialized = _serialize_quiz_formset(formset)
        self.assertEqual(serialized[0]['question'], "What is 2+2?")
        self.assertEqual(serialized[0]['correct_answer'], "4")
