import hashlib

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from rest_framework.test import APITestCase

from apps.authentication.choices import UserRoleChoices
from apps.document.models import Document

User = get_user_model()

TEST_PASSWORD = "Str0ng-pass!"

TEST_SETTINGS = {
    "STORAGES": {
        "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    },
    "CACHES": {
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
    },
    "MEDIA_URL": "/media/",
}


def make_file(
    name="doc.pdf", content=b"%PDF-1.4 test content", content_type="application/pdf"
):
    return SimpleUploadedFile(name, content, content_type=content_type)


@override_settings(**TEST_SETTINGS)
class BaseAPITestCase(APITestCase):
    def setUp(self):
        cache.clear()
        self.admin = self.make_user("admin", UserRoleChoices.ADMIN)
        self.editor = self.make_user("editor", UserRoleChoices.EDITOR)
        self.viewer = self.make_user("viewer", UserRoleChoices.VIEWER)

    @staticmethod
    def make_user(username, role=UserRoleChoices.VIEWER):
        return User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password=TEST_PASSWORD,
            role=role,
        )

    def login_as(self, user):
        self.client.force_authenticate(user=user)

    @staticmethod
    def make_document(
        owner,
        title="Doc",
        name="doc.pdf",
        content=b"%PDF-1.4 test content",
        content_type="application/pdf",
        description=None,
    ) -> Document:
        return Document.objects.create(
            owner=owner,
            title=title,
            description=description,
            file=make_file(name, content, content_type),
            file_name=name,
            content_type=content_type,
            size=len(content),
            checksum=hashlib.sha256(content).hexdigest(),
        )