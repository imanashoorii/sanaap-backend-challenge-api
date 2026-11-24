from rest_framework import status
from rest_framework.exceptions import APIException

from general.enum import UserMessages, ErrorCodes


class BaseAPIException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST


class MalformedData(BaseAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = ErrorCodes.MALFORMED_DATA
    default_detail = UserMessages.MALFORMED_DATA


class ForbiddenUpdate(BaseAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = ErrorCodes.OBJ_NOT_EDITABLE
    default_detail = UserMessages.OBJ_NOT_EDITABLE

class NotFound(BaseAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = ErrorCodes.NOT_FOUND
    default_detail = UserMessages.NOT_FOUND


class NotAllowed(BaseAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = ErrorCodes.NOT_ALLOWED
    default_detail = UserMessages.NOT_ALLOWED