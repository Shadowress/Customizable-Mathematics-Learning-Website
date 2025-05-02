from django.contrib.auth.views import LogoutView
from django.urls import path, include

from apps.users import views

urlpatterns = [
    # --- Main Page ---
    path('', views.home, name='homepage'),

    # --- Authentication ---
    path('login/', views.user_login, name='login'),
    path('signup/', views.user_signup, name='signup'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('accounts/', include('allauth.urls')),

    # --- Email Verification ---
    path('verify-email/', views.verify_email_page, name='verify_email_page'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('check-verification-status/', views.check_verification_status, name='check_verification_status'),
    path('resend-verification-email/', views.resend_verification_email, name='resend_verification_email'),

    # --- Password Reset ---
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('password-reset/verify/', views.verify_password_reset_page, name='verify_password_reset_page'),
    path('password-reset/verify/<str:token>/', views.verify_password_reset, name='verify_password_reset'),
    path('password-reset/new-password/', views.password_reset_form, name='password_reset_form'),
    path('check-password-reset-verification/', views.check_password_reset_verification,
         name='check_password_reset_verification'),
    path('resend-password-reset-verification/', views.resend_password_reset_verification,
         name='resend_password_reset_verification'),

    # --- Dashboard Views ---
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path("upload-profile-picture/", views.profile_picture_upload, name="profile_picture_upload"),
    path('content-manager-dashboard/', views.content_manager_dashboard, name='content_manager_dashboard'),
]
