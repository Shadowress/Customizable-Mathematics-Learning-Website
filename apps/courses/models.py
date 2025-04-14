import os

from django.db import models
from django.utils.text import slugify

from apps.users.models import CustomUser


# Create your models here.
def content_upload_path(instance, filename):
    """Dynamically generate file path for storing course media."""
    return os.path.join(
        "courses",
        str(instance.section.course.id),
        f"section_{instance.section.id}",
        filename
    )


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

    title: str = models.CharField(max_length=255, unique=True, blank=False, null=False)
    slug = models.SlugField(unique=True, blank=True)
    description: str = models.TextField(blank=False, null=False)
    difficulty: str = models.CharField(max_length=15, choices=DIFFICULTY_LEVELS, blank=False, null=False)
    estimated_completion_time = models.PositiveIntegerField(
        help_text="Estimated completion time in minutes",
        blank=False,
        null=False
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=DRAFT)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name="courses", null=True)

    def save(self, *args, **kwargs):
        if self.pk:
            original_course = Course.objects.get(pk=self.pk)
            if original_course.title != self.title:
                self.slug = slugify(self.title)

        if not self.slug:
            self.slug = slugify(self.title)

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.title


class Section(models.Model):
    course: 'Course' = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="sections")
    title = models.CharField(max_length=255, blank=False, null=False)
    order = models.PositiveIntegerField(default=0)

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
    video_url = models.URLField(blank=True, null=True)
    video_transcription = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.content_type.capitalize()} Content in Section {self.section.id}"

    def delete(self, *args, **kwargs):
        """Delete associated files when deleting content."""
        if self.image:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)

        super().delete(*args, **kwargs)


class Quiz(models.Model):
    section: 'Section' = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="quizzes")
    question: str = models.TextField(blank=True, null=True)
    correct_answer: str = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Quiz {self.order} in Section {self.section.order}"


class Answer(models.Model):
    user: 'CustomUser' = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="answers")
    quiz: 'Quiz' = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="answers")
    answer: str = models.TextField()

    def __str__(self) -> str:
        return f"{self.user} answered {self.quiz}"
