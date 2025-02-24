from django.contrib.auth.views import LogoutView
from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.home, name='homepage'),
    path('login/', views.login_view, name='login'),
    path('accounts/', include('allauth.urls')),
    path('signup/', views.sign_up_view, name='signup'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
