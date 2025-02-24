from django.db import models

from apps.users.models import CustomUser


# Create your models here.
class Course(models.Model):
    JUNIOR = "junior"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advance"

    DIFFICULTY_LEVELS = [
        (JUNIOR, "Junior"),
        (INTERMEDIATE, "Intermediate"),
        (ADVANCED, "Advance"),
    ]

    title: str = models.CharField(max_length=255, unique=True)
    difficulty: str = models.CharField(max_length=15, choices=DIFFICULTY_LEVELS, blank=False, null=False)

    def __str__(self) -> str:
        return self.title


class Section(models.Model):
    course: 'Course' = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="sections")

    def __str__(self) -> str:
        return f"Section of {self.course.title}"


class Content(models.Model):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"

    CONTENT_TYPES = [
        (TEXT, "Text"),
        (IMAGE, "Image"),
        (VIDEO, "Video"),
    ]

    section: 'Section' = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="contents")
    content_type: str = models.CharField(max_length=5, choices=CONTENT_TYPES)
    content_data: str = models.TextField()

    def __str__(self) -> str:
        return f"{self.get_content_type_display()} in {self.section}"


class Quiz(models.Model):
    section: 'Section' = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="quizzes")
    question: str = models.TextField()
    correct_answer: str = models.JSONField()


class Answer(models.Model):
    user: 'CustomUser' = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="answers")
    quiz: 'Quiz' = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="answers")
    answer: str = models.TextField()

    def __str__(self) -> str:
        return f"{self.user} answered {self.quiz}"
