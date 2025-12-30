import logging
from threading import local

# Thread-local storage to keep track of the current user
_user = local()


class UserFilter(logging.Filter):
    """
    A filter that injects the current user's email into the log record.
    """

    def filter(self, record):
        record.user = getattr(_user, "email", "Anonymous")
        return True


def set_current_user(email):
    _user.email = email


def clear_current_user():
    if hasattr(_user, "email"):
        del _user.email
