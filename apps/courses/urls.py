from django.urls import path

from . import views

urlpatterns = [
    # --- Normal Users ---
    path('<slug:slug>/', views.course, name='course'),

    # --- Content Managers ---
    path('create-course/', views.create_course, name='create_course'),
    path('edit-course/<slug:slug>/', views.edit_course, name='edit_course'),
]
