from django.test import TestCase

from apps.courses.forms import CourseForm, SectionForm, TextContentForm, QuizForm
from apps.courses.models import Content


class CourseFormTest(TestCase):
    def test_course_form_valid(self):
        form_data = {
            'title': 'Test Course',
            'description': 'This is a test course.',
            'difficulty': 'junior',
            'estimated_completion_time': 30
        }
        form = CourseForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_course_form_invalid_missing_title(self):
        form_data = {
            'title': '',  # Required
            'description': 'No title course.',
            'difficulty': 'junior',
            'estimated_completion_time': 30
        }
        form = CourseForm(data=form_data)
        self.assertFalse(form.is_valid())


class SectionFormTest(TestCase):
    def test_section_form_valid(self):
        form_data = {
            'title': 'Intro Section',
            'order': 1,
        }
        form = SectionForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_section_form_invalid_missing_title(self):
        form_data = {
            'title': '',  # Required
            'order': 1,
        }
        form = SectionForm(data=form_data)
        self.assertFalse(form.is_valid())


class TextContentFormTest(TestCase):
    def test_text_content_form_valid_empty_text(self):
        # Allowed for draft
        form_data = {
            'content_type': Content.TEXT,
            'text_content': '',
            'order': 0,
            'section_order': 0
        }
        form = TextContentForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_text_content_form_valid_with_text(self):
        form_data = {
            'content_type': Content.TEXT,
            'text_content': 'Some content',
            'order': 0,
            'section_order': 0
        }
        form = TextContentForm(data=form_data)
        self.assertTrue(form.is_valid())


class QuizFormTest(TestCase):
    def test_quiz_form_valid_empty_fields(self):
        # Allowed for draft
        form_data = {
            'question': '',
            'correct_answer': '',
            'order': 0,
            'section_order': 0
        }
        form = QuizForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_quiz_form_valid_with_question(self):
        form_data = {
            'question': 'What is 2 + 2?',
            'correct_answer': '4',
            'order': 0,
            'section_order': 0
        }
        form = QuizForm(data=form_data)
        self.assertTrue(form.is_valid())
