from django.utils import timezone

from apps.courses.models import ScheduledCourse
from apps.users.utils import send_email


def send_scheduled_notifications():
    now = timezone.now()
    upcoming_courses = ScheduledCourse.objects.filter(notification_sent=False)

    for sc in upcoming_courses:
        notify_time = sc.get_notification_time()

        if notify_time <= now:
            try:
                send_email(
                    user=sc.user,
                    purpose="scheduled_course_reminder",
                    extra_context={
                        "course_title": sc.course.title,
                        "scheduled_time": sc.scheduled_time
                    }
                )
                sc.notification_sent = True
                sc.save(update_fields=["notification_sent"])
            except Exception as e:
                print(f"[ERROR] Failed to send email to user {sc.user.id}: {e}")
