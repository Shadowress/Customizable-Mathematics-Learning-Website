from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.courses.models import ScheduledCourse, Course
from apps.courses.tasks import send_scheduled_notifications


class SendScheduledNotificationsTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='password123',
            email='testuser@example.com',
            role='normal',
            is_verified=True
        )
        self.course = Course.objects.create(
            title="Test Course",
            description="Test description",
            difficulty="junior",
            estimated_completion_time=30
        )
        self.scheduled_course = ScheduledCourse.objects.create(
            user=self.user,
            course=self.course,
            scheduled_time=timezone.now() - timezone.timedelta(hours=1),
            notification_sent=False
        )

    def test_send_scheduled_notifications_marks_as_sent(self):
        send_scheduled_notifications()
        self.scheduled_course.refresh_from_db()
        self.assertTrue(self.scheduled_course.notification_sent)

    def test_send_scheduled_notifications_skips_future_notifications(self):
        future_scheduled_course = ScheduledCourse.objects.create(
            user=self.user,
            course=self.course,
            scheduled_time=timezone.now() + timezone.timedelta(hours=1),
            notification_sent=False
        )

        send_scheduled_notifications()
        future_scheduled_course.refresh_from_db()
        self.assertFalse(future_scheduled_course.notification_sent)
