from rest_framework import permissions


class IsVerifiedResearcher(permissions.BasePermission):
    """
    Allows only Community or Institutionally Verified researchers
    to validate observations.
    """

    message = "Only verified researchers can validate observations."

    def has_permission(self, request, view):
        user = request.user
        if user and user.is_authenticated:
            return user.is_staff or user.is_verified_researcher
        return False


class IsInstitutionalResearcher(permissions.BasePermission):
    """
    Allows only Institutionally Verified researchers for sensitive operations.
    Use this for features like bulk exports, advanced API access, etc.
    """

    message = "This action requires institutional researcher verification."

    def has_permission(self, request, view):
        user = request.user
        if user and user.is_authenticated:
            from users.models import User

            return user.is_staff or user.role == User.RESEARCHER_INSTITUTIONAL
        return False


class IsPendingResearcher(permissions.BasePermission):
    """
    Check if user is a pending researcher (for specific endpoints).
    """

    message = "This action is only available to pending researchers."

    def has_permission(self, request, view):
        user = request.user
        if user and user.is_authenticated:
            from users.models import User

            return user.role == User.RESEARCHER_PENDING
        return False
