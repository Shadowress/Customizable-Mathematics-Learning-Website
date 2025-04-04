from django import forms
from django.forms import inlineformset_factory

from apps.courses.models import Course, Section, Content, Quiz


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'difficulty', 'estimated_completion_time']


class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        exclude = ['section_number', 'course']


class TextContentForm(forms.ModelForm):
    class Meta:
        model = Content
        fields = ['content_type', 'text_content']
        widgets = {
            'text_content': forms.Textarea(attrs={'placeholder': 'Enter your text content here...'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:  # Ensure it's a new content object
            self.fields['content_type'].initial = Content.TEXT  # Set default value to 'text'
            self.fields['content_type'].widget = forms.HiddenInput()  # Hide the field so it's not editable


class ImageContentForm(forms.ModelForm):
    class Meta:
        model = Content
        fields = ['content_type', 'image', 'alt_text']
        widgets = {
            'alt_text': forms.TextInput(attrs={'placeholder': 'Alternative text for the image (optional)'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:  # Ensure it's a new content object
            self.fields['content_type'].initial = Content.IMAGE  # Set default value to 'image'
            self.fields['content_type'].widget = forms.HiddenInput()  # Hide the field so it's not editable


class VideoContentForm(forms.ModelForm):
    class Meta:
        model = Content
        fields = ['content_type', 'video', 'video_transcription']
        widgets = {
            'video_transcription': forms.Textarea(attrs={'placeholder': 'Transcription for the video (optional)'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:  # Ensure it's a new content object
            self.fields['content_type'].initial = Content.VIDEO  # Set default value to 'video'
            self.fields['content_type'].widget = forms.HiddenInput()  # Hide the field so it's not editable


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['question', 'correct_answer']


# Inline formset for Section and its contents (text, image, or video)
SectionFormSet = inlineformset_factory(
    Course,
    Section,
    form=SectionForm,
    extra=1,
    can_delete=True
)

TextContentInlineFormSet = inlineformset_factory(
    Section,
    Content,
    form=TextContentForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)

ImageContentInlineFormSet = inlineformset_factory(
    Section,
    Content,
    form=ImageContentForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)

VideoContentInlineFormSet = inlineformset_factory(
    Section,
    Content,
    form=VideoContentForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)

QuizFormSet = inlineformset_factory(
    Section,
    Quiz,
    form=QuizForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)
