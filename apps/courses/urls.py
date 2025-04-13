from django.urls import path

from . import views

urlpatterns = [
    # --- Content Managers ---
    path('create-course/', views.create_or_edit_course, name='create_course'),
    path('edit-course/<slug:slug>/', views.create_or_edit_course, name='edit_course'),

    # --- Normal Users ---
    path('<slug:slug>/', views.course, name='course'),
]
