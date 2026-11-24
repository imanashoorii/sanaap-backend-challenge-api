from rest_framework import status

from apps.base.exceptions import BaseAPIException
from general.enum import UserMessages, ErrorCodes


class FileTooLargeException(BaseAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = ErrorCodes.FILE_TOO_LARGE
    default_detail = UserMessages.FILE_TOO_LARGE


class UnsupportedFileTypeException(BaseAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = ErrorCodes.UNSUPPORTED_FILE_TYPE
    default_detail = UserMessages.UNSUPPORTED_FILE_TYPE


class DocumentNotFoundException(BaseAPIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_code = ErrorCodes.DOCUMENT_NOT_FOUND
    default_detail = UserMessages.DOCUMENT_NOT_FOUND