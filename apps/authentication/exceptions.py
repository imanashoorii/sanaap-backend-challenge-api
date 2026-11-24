from rest_framework import status

from apps.base.exceptions import BaseAPIException
from general.enum import UserMessages, ErrorCodes


class InvalidCredentials(BaseAPIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_code = ErrorCodes.INVALID_CREDENTIALS
    default_detail = UserMessages.INVALID_CREDENTIALS
