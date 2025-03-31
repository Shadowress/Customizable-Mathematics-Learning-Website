from django.urls import path

from . import views

urlpatterns = [
    path('<int:course_id>/', views.course, name='course'),

    path('create-course/', views.create_course, name='create_course')
]
