# Register your models here.
from django.contrib import admin

from .models import Course, Section, Content, Quiz, Answer

# todo remove during production
admin.site.register(Course)
admin.site.register(Section)
admin.site.register(Content)
admin.site.register(Quiz)
admin.site.register(Answer)
