import os
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from django.utils.text import slugify

from apps.courses.models import Course, Section, Content, Quiz, Answer, ScheduledCourse
from apps.users.models import CustomUser


class CourseModelTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='creator',
            email='creator@example.com',
            password='testpass'
        )
        self.course = Course.objects.create(
            title="My First Course",
            description="A simple test course",
            difficulty=Course.JUNIOR,
            estimated_completion_time=30,
            status=Course.DRAFT,
            created_by=self.user
        )

    def test_course_slug_is_generated(self):
        self.assertEqual(self.course.slug, slugify("My First Course"))

    def test_course_str(self):
        self.assertEqual(str(self.course), "My First Course")

    def test_section_creation(self):
        section = Section.objects.create(course=self.course, title="Intro", order=1)
        self.assertEqual(str(section), f"Section 1 of {self.course.title}")

    def test_content_creation_text(self):
        section = Section.objects.create(course=self.course, title="Intro", order=1)
        content = Content.objects.create(section=section, content_type=Content.TEXT, text_content="Hello world")
        self.assertEqual(str(content), f"Text Content in Section {section.id}")

    def test_content_delete_image_file(self):
        section = Section.objects.create(course=self.course, title="Intro", order=1)

        temp_file = tempfile.NamedTemporaryFile(suffix=".jpg").name
        uploaded_file = SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")

        content = Content.objects.create(
            section=section,
            content_type=Content.IMAGE,
            image=uploaded_file
        )
        image_path = content.image.path
        content.delete()
        self.assertFalse(os.path.exists(image_path))  # File should be deleted

    def test_quiz_and_answer(self):
        section = Section.objects.create(course=self.course, title="Quiz Section", order=1)
        quiz = Quiz.objects.create(section=section, question="2 + 2?", correct_answer="4", order=1)
        answer = Answer.objects.create(user=self.user, quiz=quiz)

        self.assertEqual(str(quiz), f"Quiz 1 in Section 1")
        self.assertEqual(str(answer), f"{self.user} answered {quiz}")

    def test_scheduled_course_and_notification_time(self):
        now = timezone.now()
        scheduled = ScheduledCourse.objects.create(
            user=self.user,
            course=self.course,
            scheduled_time=now + timezone.timedelta(hours=1),
            notify_before_minutes=15
        )
        self.assertEqual(str(scheduled), f"{self.user.username} - {self.course.title} at {scheduled.scheduled_time}")
        expected_notify_time = scheduled.scheduled_time - timezone.timedelta(minutes=15)
        self.assertEqual(scheduled.get_notification_time(), expected_notify_time)
