from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from django.contrib.auth import views as auth_views

from . import views
from .views import EmailTokenObtainPairView

urlpatterns = [
    path(
        "login/", EmailTokenObtainPairView.as_view(), name="token_obtain_pair"
    ),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("register/", views.RegisterView.as_view(), name="auth_register"),
    path("user/", views.UserDetailView.as_view(), name="auth_user"),
    path("profiles/me/", views.ProfileMeView.as_view(), name="profile_me"),
    path("logout/", views.LogoutView.as_view(), name="auth_logout"),
    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(
            template_name="users/password_reset_form.html",
            email_template_name="users/password_reset_email.html",
            subject_template_name="users/password_reset_subject.txt",
        ),
        name="password_reset",
    ),
    path(
        "password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="users/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="users/password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="users/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    # DRF API endpoints for password reset (relative to where it's included)
    # These will be under 'api/v1/users/' because of how api.urls is set up
    path(
        "password-reset/",
        views.PasswordResetAPIView.as_view(),
        name="api_password_reset",
    ),
    path(
        "password-reset/confirm/",
        views.PasswordResetConfirmAPIView.as_view(),
        name="api_password_reset_confirm",
    ),
    path(
        "verify-email/",
        views.EmailVerificationAPIView.as_view(),
        name="api_email_verification",
    ),
    path(
        "researcher/complete-profile/",
        views.CompleteResearcherProfileView.as_view(),
        name="complete_researcher_profile",
    ),
]
