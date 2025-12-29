from django.conf import settings
from django.contrib.auth import get_user_model, logout
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


class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200 and "access" in response.data:
            access_token = response.data["access"]
            response.set_cookie(
                key="access_token",
                value=access_token,
                httponly=True,
                secure=not settings.DEBUG,
                samesite="Lax",
                max_age=24 * 60 * 60,
                path="/",
            )
        return response


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):

        # Perform Django's built-in logout to invalidate the session
        logout(request)

        resp = Response({"detail": "Logged out"}, status=200)

        # Common cookie attributes for deletion
        cookie_path = settings.SIMPLE_JWT.get("AUTH_COOKIE_PATH", "/")
        # Explicitly set domain for localhost in development for robust deletion
        cookie_domain = (
            "localhost"
            if settings.DEBUG
            else settings.SIMPLE_JWT.get("AUTH_COOKIE_DOMAIN", None)
        )
        cookie_samesite = settings.SIMPLE_JWT.get(
            "AUTH_COOKIE_SAMESITE", "Lax"
        )

        # Delete access_token cookie
        access_cookie_name = settings.SIMPLE_JWT["AUTH_COOKIE"]
        resp.delete_cookie(
            access_cookie_name,
            path=cookie_path,
            domain=cookie_domain,
            samesite=cookie_samesite,
        )

        # Delete refresh_token cookie
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
    permission_classes = (
        AllowAny,
    )  # Uncomment if you want to allow unauthenticated access

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
    permission_classes = (
        AllowAny,
    )  # Uncomment if you want to allow unauthenticated access

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
        return Response(
            {"detail": "Email has been verified successfully."},
            status=status.HTTP_200_OK,
        )
