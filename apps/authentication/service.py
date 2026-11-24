from django.contrib.auth import get_user_model

from general.enum import UserMessages
from general.validations import validate_email

User = get_user_model()


class UserServices:

    @staticmethod
    def retrieve_user_by_identifier(identifier: str) -> tuple[bool, str]:
        """
        Retrieve a user's username by identifier (email or username).
        """
        if validate_email(identifier):
            user = User.objects.filter(email__iexact=identifier).first()
        else:
            user = User.objects.filter(username=identifier).first()

        if not user:
            return False, UserMessages.INVALID_CREDENTIALS

        return True, user.username