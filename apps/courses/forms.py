import re

from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory, TextInput

from apps.courses.models import Course, Section, Content, Quiz


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'difficulty', 'estimated_completion_time']


class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = ['title', 'order']
        widgets = {
            'title': TextInput(attrs={'required': 'required'}),
            'order': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].required = True


class TextContentForm(forms.ModelForm):
    section_order = forms.IntegerField(widget=forms.HiddenInput(), required=False, min_value=0)

    class Meta:
        model = Content
        fields = ['content_type', 'text_content', 'order']
        widgets = {
            'text_content': forms.Textarea(attrs={'placeholder': 'Enter your text content here...'}),
            'order': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['content_type'].initial = Content.TEXT
            self.fields['content_type'].widget = forms.HiddenInput()


class ImageContentForm(forms.ModelForm):
    section_order = forms.IntegerField(widget=forms.HiddenInput(), required=False, min_value=0)

    class Meta:
        model = Content
        fields = ['content_type', 'image', 'alt_text', 'order']
        widgets = {
            'alt_text': forms.TextInput(attrs={'placeholder': 'Alternative text for the image (optional)'}),
            'order': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['content_type'].initial = Content.IMAGE
            self.fields['content_type'].widget = forms.HiddenInput()


class VideoContentForm(forms.ModelForm):
    section_order = forms.IntegerField(widget=forms.HiddenInput(), required=False, min_value=0)

    class Meta:
        model = Content
        fields = ['content_type', 'video_url', 'video_transcription', 'order']
        widgets = {
            'video_url': forms.URLInput(
                attrs={'placeholder': 'YouTube video URL', 'pattern': r'https?://(www\.)?(youtube\.com|youtu\.be)/.+',
                       'title': 'Only YouTube URLs allowed'}
            ),
            'video_transcription': forms.HiddenInput(),
            'order': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['content_type'].initial = Content.VIDEO
            self.fields['content_type'].widget = forms.HiddenInput()

    def clean_video_url(self):
        url = self.cleaned_data.get("video_url")
        youtube_regex = re.compile(
            r'^(https?\:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+$'
        )
        if url and not youtube_regex.match(url):
            raise ValidationError("Only YouTube URLs are allowed.")
        return url


class QuizForm(forms.ModelForm):
    section_order = forms.IntegerField(widget=forms.HiddenInput(), required=False, min_value=0)

    class Meta:
        model = Quiz
        fields = ['question', 'correct_answer', 'order']
        widgets = {
            'order': forms.HiddenInput(),
        }


# Inline formset for Section and its contents (text, image, or video)
SectionFormSet = inlineformset_factory(
    Course,
    Section,
    form=SectionForm,
    extra=0,
    can_delete=True,
)

TextContentFormSet = inlineformset_factory(
    Section,
    Content,
    form=TextContentForm,
    extra=0,
    can_delete=True,
)

ImageContentFormSet = inlineformset_factory(
    Section,
    Content,
    form=ImageContentForm,
    extra=0,
    can_delete=True,
)

VideoContentFormSet = inlineformset_factory(
    Section,
    Content,
    form=VideoContentForm,
    extra=0,
    can_delete=True,
)

QuizFormSet = inlineformset_factory(
    Section,
    Quiz,
    form=QuizForm,
    extra=0,
    can_delete=True,
)
