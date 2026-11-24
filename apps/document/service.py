import hashlib
import os

from apps.base.exceptions import MalformedData
from apps.document.exceptions import (
    FileTooLargeException,
    UnsupportedFileTypeException,
)
from general.constants import MAX_DOCUMENT_SIZE, ALLOWED_DOCUMENT_CONTENT_TYPES


class DocumentServices:
    @staticmethod
    def validate_file(file) -> None:
        if file.size == 0:
            raise MalformedData()
        if file.size > MAX_DOCUMENT_SIZE:
            raise FileTooLargeException()
        if file.content_type not in ALLOWED_DOCUMENT_CONTENT_TYPES:
            raise UnsupportedFileTypeException()

    @staticmethod
    def get_file_metadata(file) -> dict:
        sha256 = hashlib.sha256()
        for chunk in file.chunks():
            sha256.update(chunk)
        file.seek(0)

        return {
            "file_name": os.path.basename(file.name)[:255],
            "content_type": file.content_type,
            "size": file.size,
            "checksum": sha256.hexdigest(),
        }