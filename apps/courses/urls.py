from django.urls import path

from . import views

urlpatterns = [
    # --- Content Managers ---
    path('create-course/', views.create_or_edit_course, name='create_course'),
    path('edit-course/<slug:slug>/', views.create_or_edit_course, name='edit_course'),
    path('transcribe-video/', views.transcribe_video, name='transcribe_video'),

    # --- Normal Users ---
    path('submit-quiz-answer/', views.submit_quiz_answer, name='submit_quiz_answer'),
    path('toggle-save-course/<int:course_id>/', views.toggle_save_course, name='toggle_save_course'),
    path('schedule-course/<int:course_id>/', views.schedule_course, name='schedule_course'),
    path('<slug:slug>/', views.course, name='course'),
]
