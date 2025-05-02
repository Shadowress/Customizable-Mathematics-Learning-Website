import os
import tempfile

import whisper
import yt_dlp
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.courses.models import Course, Section, Content, Quiz

User = get_user_model()


class Command(BaseCommand):
    help = "Load meaningful test data for courses, sections, content, and quizzes."

    def handle(self, *args, **kwargs):
        self.stdout.write("📦 Loading demo data...")

        alice = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="testpass123",
            role="content_manager",
            is_active=True,
            is_verified=True
        )

        self.create_basic_arithmetic_course(alice)
        self.create_shapes_and_patterns_course(alice)

        self.stdout.write(self.style.SUCCESS("✅ Demo courses and content have been loaded."))
        self.stdout.write("Test Content Manager created")
        self.stdout.write("Email: alice@example.com")
        self.stdout.write("Password: testpass123")

    def create_basic_arithmetic_course(self, user):
        course = Course.objects.create(
            title="Basic Arithmetic for Beginners",
            slug=slugify("Basic Arithmetic for Beginners"),
            description="Learn the foundations of arithmetic including addition, subtraction, and number sense.",
            difficulty=Course.JUNIOR,
            estimated_completion_time=40,
            status=Course.PUBLISHED,
            created_by=user
        )

        # Section 1
        s1 = Section.objects.create(course=course, title="Understanding Numbers and Counting", order=0)
        Content.objects.create(section=s1, content_type=Content.TEXT, text_content="""
            Numbers are symbols used to count, measure, and label.
            We start with numbers like 1, 2, 3... all the way to 10 and beyond.
            Counting helps us understand quantity.
        """, order=0)
        Quiz.objects.create(section=s1, question="What number comes after 4?", correct_answer="5", order=0)
        Quiz.objects.create(section=s1, question="How many fingers do you have?", correct_answer="10", order=1)

        # Section 2
        s2 = Section.objects.create(course=course, title="Basic Addition and Subtraction", order=1)
        Content.objects.create(section=s2, content_type=Content.TEXT, text_content="""
            Addition is the process of putting things together.
            Subtraction is taking things away.
            Example: 2 + 3 = 5, and 5 - 3 = 2.
        """, order=0)

        videos = [
            "https://www.youtube.com/embed/VScM8Z8Jls0?si=P0Z3UyDb6a4eIVXG",
            "https://www.youtube.com/embed/YLPbduEc4sA?si=mCS07ilgwURYLfVO"
        ]
        for idx, video_url in enumerate(videos, start=1):
            Content.objects.create(
                section=s2,
                content_type=Content.VIDEO,
                video_url=video_url,
                video_transcription=self.transcribe_video_url(video_url),
                order=idx
            )

        Quiz.objects.create(section=s2, question="2 + 3 = ?", correct_answer="5", order=0)
        Quiz.objects.create(section=s2, question="7 - 4 = ?", correct_answer="3", order=1)

        # Section 3
        s3 = Section.objects.create(course=course, title="Multiplication and Division", order=2)
        Content.objects.create(
            section=s3,
            content_type=Content.TEXT,
            text_content=(
                "Multiplication is repeated addition. For example, 3 × 4 means adding 3 four times (3+3+3+3=12).\n"
                "Division is splitting a number into equal parts. For example, 12 ÷ 3 splits 12 into 3 equal groups (4 in each)."
            ),
            order=0
        )

        mult_videos = [
            "https://www.youtube.com/embed/FJ5qLWP3Fqo?si=caTHdQWYJMjmHumW",
            "https://www.youtube.com/embed/KGMf314LUc0?si=tXdiE1wU-Zc3caPk"
        ]
        for idx, video_url in enumerate(mult_videos, start=1):
            Content.objects.create(
                section=s3,
                content_type=Content.VIDEO,
                video_url=video_url,
                video_transcription=self.transcribe_video_url(video_url),
                order=idx
            )

        Quiz.objects.create(section=s3, question="What is 6 × 3?", correct_answer="18", order=0)
        Quiz.objects.create(section=s3, question="If you divide 20 by 4, what is the result?", correct_answer="5",
                            order=1)

    def create_shapes_and_patterns_course(self, user):
        course = Course.objects.create(
            title="Learning Shapes and Patterns",
            slug=slugify("Learning Shapes and Patterns"),
            description="Identify common shapes and understand basic repeating patterns.",
            difficulty=Course.JUNIOR,
            estimated_completion_time=35,
            status=Course.DRAFT,
            created_by=user
        )

        # Section 1
        s1 = Section.objects.create(course=course, title="Recognizing Basic Shapes", order=0)
        Content.objects.create(section=s1, content_type=Content.TEXT, text_content="""
            Shapes are all around us. A circle is round, a square has 4 equal sides, and a triangle has 3 sides.
            We can find shapes in objects like balls, boxes, and road signs.
        """, order=0)

        video_url = "https://www.youtube.com/embed/o-6OKWU99Co?si=JtyzgbLP8GMbQ_Jx"
        Content.objects.create(
            section=s1,
            content_type=Content.VIDEO,
            video_url=video_url,
            video_transcription=self.transcribe_video_url(video_url),
            order=1
        )

        Quiz.objects.create(section=s1, question="How many sides does a triangle have?", correct_answer="3", order=0)
        Quiz.objects.create(section=s1, question="What shape is a stop sign?", correct_answer="Octagon", order=1)

        # Section 2
        s2 = Section.objects.create(course=course, title="Identifying Patterns", order=1)
        Content.objects.create(section=s2, content_type=Content.TEXT, text_content="""
            A pattern is something that repeats in a specific order.
            Example: red, blue, red, blue... This is a color pattern.
            Patterns help us make predictions.
        """, order=0)

        video_url = "https://www.youtube.com/embed/CzFLDtvN_Xk?si=tzwy_FP30ozcBsRA"
        Content.objects.create(
            section=s2,
            content_type=Content.VIDEO,
            video_url=video_url,
            video_transcription=self.transcribe_video_url(video_url),
            order=1
        )

        Quiz.objects.create(section=s2, question="What comes next: circle, square, circle, square...?",
                            correct_answer="circle", order=0)
        Quiz.objects.create(section=s2,
                            question="Which of the following is a pattern? A) apple, banana, apple, banana B) red, red, blue, green",
                            correct_answer="A", order=1)

    def transcribe_video_url(self, video_url):
        """Downloads and transcribes a YouTube video using Whisper."""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                audio_path = os.path.join(temp_dir, "audio.wav")

                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': os.path.join(temp_dir, 'audio.%(ext)s'),
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'wav',
                        'preferredquality': '192',
                    }],
                    'quiet': True,
                    'no_warnings': True,
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([video_url])

                for file in os.listdir(temp_dir):
                    if file.endswith(".wav"):
                        audio_path = os.path.join(temp_dir, file)
                        break
                else:
                    raise FileNotFoundError("Audio file not found after download.")

                model = whisper.load_model("base")
                result = model.transcribe(audio_path)

                return [
                    {
                        "start_time": int(segment.get("start", 0.0)),
                        "end_time": int(segment.get("end", 0.0)),
                        "text": segment.get("text", "").strip()
                    }
                    for segment in result.get("segments", [])
                ]

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Transcription failed: {str(e)}"))
            return None
