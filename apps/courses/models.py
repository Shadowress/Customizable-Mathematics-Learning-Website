import os

from django.db import models

from apps.users.models import CustomUser


# Create your models here.
def content_upload_path(instance, filename):
    """Dynamically generate file path for storing course media."""
    return f"courses/{instance.section.course.id}/section_{instance.section.id}/{filename}"


class Course(models.Model):
    JUNIOR = "junior"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advance"

    DIFFICULTY_LEVELS = [
        (JUNIOR, "Junior"),
        (INTERMEDIATE, "Intermediate"),
        (ADVANCED, "Advance"),
    ]

    DRAFT = "draft"
    PUBLISHED = "published"

    STATUS_CHOICES = [
        (DRAFT, "Draft"),
        (PUBLISHED, "Published"),
    ]

    title: str = models.CharField(max_length=255, unique=True)
    description: str = models.TextField(blank=True)
    difficulty: str = models.CharField(max_length=15, choices=DIFFICULTY_LEVELS, blank=False, null=False)
    estimated_completion_time = models.PositiveIntegerField(
        help_text="Estimated completion time in minutes",
        null=True,
        blank=True
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=DRAFT)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name="courses", null=True)

    def __str__(self) -> str:
        return self.title


class Section(models.Model):
    course: 'Course' = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="sections")
    order = models.PositiveIntegerField(editable=False)

    class Meta:
        ordering = ["order"]

    def save(self, *args, **kwargs):
        if not self.order:
            self.order = self.course.sections.count() + 1
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Section {self.order} of {self.course.title}"


class Content(models.Model):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"

    CONTENT_TYPES = [
        (TEXT, "Text"),
        (IMAGE, "Image"),
        (VIDEO, "Video"),
    ]

    section = models.ForeignKey('Section', on_delete=models.CASCADE, related_name="contents")
    content_type = models.CharField(max_length=5, choices=CONTENT_TYPES)
    text_content = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to=content_upload_path, blank=True, null=True)
    alt_text = models.CharField(max_length=255, blank=True, null=True)
    video = models.FileField(upload_to=content_upload_path, blank=True, null=True)
    video_transcription = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def save(self, *args, **kwargs):
        """Set the order automatically if not provided."""
        if not self.order:
            self.order = self.section.contents.count() + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.content_type.capitalize()} Content in Section {self.section.id}"

    def delete(self, *args, **kwargs):
        """Delete associated files when deleting content."""
        if self.image:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)
        if self.video:
            if os.path.isfile(self.video.path):
                os.remove(self.video.path)
        super().delete(*args, **kwargs)


class Quiz(models.Model):
    section: 'Section' = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="quizzes")
    question: str = models.TextField()
    correct_answer: str = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def save(self, *args, **kwargs):
        if not self.order:
            self.order = self.section.quizzes.count() + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Quiz {self.order} in Section {self.section.order}"


class Answer(models.Model):
    user: 'CustomUser' = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="answers")
    quiz: 'Quiz' = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="answers")
    answer: str = models.TextField()

    def __str__(self) -> str:
        return f"{self.user} answered {self.quiz}"
