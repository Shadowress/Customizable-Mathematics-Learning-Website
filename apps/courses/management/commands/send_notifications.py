from django.core.management.base import BaseCommand

from apps.courses.tasks import send_scheduled_notifications


class Command(BaseCommand):
    help = 'Send scheduled course notifications.'

    def handle(self, *args, **kwargs):
        send_scheduled_notifications()
