from django.conf import settings
from django.contrib.auth import get_user_model, logout, login
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny

from .serializers import (
    EmailTokenObtainPairSerializer,
    RegisterSerializer,
    UserProfileSerializer,
    UserSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    EmailVerificationSerializer,
    ResearcherProfileSerializer,
)


class RegisterView(generics.CreateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class UserDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class ProfileMeView(generics.RetrieveAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class CompleteResearcherProfileView(generics.UpdateAPIView):
    """
    Endpoint for researchers to complete their profile after email verification.
    """

    serializer_class = ResearcherProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        user = self.request.user

        # Only allow pending researchers to complete profile
        if not (
            user.role == get_user_model().RESEARCHER_PENDING
            or user.needs_researcher_profile_completion
        ):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "This endpoint is only for pending researchers."
            )

        # Ensure email is verified
        if not user.email_verified:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "Please verify your email before completing your profile."
            )

        return user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = (
            self.get_object()
        )  # This gets the user as 'researcher_pending' initially
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(
            serializer
        )  # This calls serializer.save() and updates the user (e.g., to 'researcher_community')

        # Access the updated user object directly from the serializer's instance
        user = serializer.instance

        response = Response(serializer.data, status=status.HTTP_200_OK)

        # Check if user was auto-approved
        if user.role == get_user_model().RESEARCHER_COMMUNITY:
            response.data["message"] = (
                "Profile completed and automatically verified! "
                "You can now validate observations."
            )
        else:
            response.data["message"] = (
                "Profile completed! Your account is pending admin review. "
                "You will be notified once approved."
            )

        return response


class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200 and "access" in response.data:
            access_token = response.data["access"]

            # Get settings from SIMPLE_JWT config
            jwt_settings = settings.SIMPLE_JWT

            response.set_cookie(
                key=jwt_settings.get("AUTH_COOKIE", "access_token"),
                value=access_token,
                httponly=jwt_settings.get("AUTH_COOKIE_HTTP_ONLY", True),
                secure=jwt_settings.get(
                    "AUTH_COOKIE_SECURE", not settings.DEBUG
                ),
                samesite=jwt_settings.get("AUTH_COOKIE_SAMESITE", "Lax"),
                domain=jwt_settings.get("AUTH_COOKIE_DOMAIN"),
                max_age=24 * 60 * 60,
                path=jwt_settings.get("AUTH_COOKIE_PATH", "/"),
            )
        return response


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logout(request)
        resp = Response({"detail": "Logged out"}, status=200)

        cookie_path = settings.SIMPLE_JWT.get("AUTH_COOKIE_PATH", "/")
        cookie_domain = (
            "localhost"
            if settings.DEBUG
            else settings.SIMPLE_JWT.get("AUTH_COOKIE_DOMAIN", None)
        )
        cookie_samesite = settings.SIMPLE_JWT.get(
            "AUTH_COOKIE_SAMESITE", "Lax"
        )

        access_cookie_name = settings.SIMPLE_JWT["AUTH_COOKIE"]
        resp.delete_cookie(
            access_cookie_name,
            path=cookie_path,
            domain=cookie_domain,
            samesite=cookie_samesite,
        )

        refresh_cookie_name = settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"]
        resp.delete_cookie(
            refresh_cookie_name,
            path=cookie_path,
            domain=cookie_domain,
            samesite=cookie_samesite,
        )

        return resp


class PasswordResetAPIView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Password reset email has been sent."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmAPIView(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {"detail": "Password has been reset with the new password."},
            status=status.HTTP_200_OK,
        )


class EmailVerificationAPIView(generics.GenericAPIView):
    serializer_class = EmailVerificationSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        login(request, user)

        # Return user info including whether they need to complete profile
        return Response(
            {
                "detail": "Email has been verified successfully.",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "role": user.role,
                    "needs_researcher_profile_completion": (
                        user.needs_researcher_profile_completion
                    ),
                },
            },
            status=status.HTTP_200_OK,
        )
