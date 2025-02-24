from django.urls import path

from . import views

urlpatterns = [
    # todo can add redirection for content-manager to their dashboard
    path('', views.dashboard, name='dashboard'),

    path('content-manager/', views.content_manager_dashboard, name='content_manager_dashboard'),
]
