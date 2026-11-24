import hashlib
from unittest import mock

from django.core.files.storage import default_storage
from django.test import SimpleTestCase
from django.urls import reverse

from apps.base.exceptions import MalformedData
from apps.base.testing import BaseAPITestCase, make_file
from apps.document.exceptions import (
    FileTooLargeException,
    UnsupportedFileTypeException,
)
from apps.document.models import Document
from apps.document.service import DocumentServices
from general.enum import ErrorCodes


class DocumentServicesTests(SimpleTestCase):
    def test_valid_file_passes(self):
        DocumentServices.validate_file(make_file())

    def test_empty_file(self):
        with self.assertRaises(MalformedData):
            DocumentServices.validate_file(make_file(content=b""))

    def test_file_too_large(self):
        with mock.patch("apps.document.service.MAX_DOCUMENT_SIZE", 10):
            with self.assertRaises(FileTooLargeException):
                DocumentServices.validate_file(make_file(content=b"x" * 11))

    def test_unsupported_content_type(self):
        with self.assertRaises(UnsupportedFileTypeException):
            DocumentServices.validate_file(
                make_file("a.exe", b"MZ", "application/x-msdownload")
            )

    def test_metadata_and_file_pointer_reset(self):
        content = b"hello world"
        file = make_file("hello.pdf", content)
        metadata = DocumentServices.get_file_metadata(file)
        self.assertEqual(metadata["file_name"], "hello.pdf")
        self.assertEqual(metadata["size"], len(content))
        self.assertEqual(metadata["checksum"], hashlib.sha256(content).hexdigest())
        self.assertEqual(file.read(), content)


class DocumentAPITestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.list_url = reverse("documents-list")

    def detail_url(self, document):
        return reverse("documents-detail", kwargs={"pk": document.pk})

    def upload(self, **file_kwargs):
        return self.client.post(
            self.list_url,
            {"title": "Report", "description": "Q3", "file": make_file(**file_kwargs)},
            format="multipart",
        )


class DocumentPermissionTests(DocumentAPITestCase):
    def test_anonymous_has_no_access(self):
        self.assertEqual(self.client.get(self.list_url).status_code, 401)
        self.assertEqual(self.upload().status_code, 401)

    def test_viewer_can_only_read(self):
        doc = self.make_document(self.admin)
        self.login_as(self.viewer)
        self.assertEqual(self.client.get(self.list_url).status_code, 200)
        self.assertEqual(self.client.get(self.detail_url(doc)).status_code, 200)

        response = self.upload()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["code"], ErrorCodes.PERMISSION_DENIED)
        self.assertEqual(
            self.client.patch(
                self.detail_url(doc), {"title": "x"}, format="multipart"
            ).status_code,
            403,
        )
        self.assertEqual(self.client.delete(self.detail_url(doc)).status_code, 403)
        self.assertEqual(Document.objects.count(), 1)

    def test_editor_can_upload_and_update_but_not_delete(self):
        self.login_as(self.editor)
        created = self.upload()
        self.assertEqual(created.status_code, 201)

        doc = Document.objects.get(pk=created.data["id"])
        updated = self.client.patch(
            self.detail_url(doc), {"title": "Renamed"}, format="multipart"
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(self.client.delete(self.detail_url(doc)).status_code, 403)
        self.assertTrue(Document.objects.filter(pk=doc.pk).exists())

    def test_admin_can_delete(self):
        doc = self.make_document(self.editor)
        self.login_as(self.admin)
        self.assertEqual(self.client.delete(self.detail_url(doc)).status_code, 204)


class DocumentCreateTests(DocumentAPITestCase):
    def setUp(self):
        super().setUp()
        self.login_as(self.editor)

    def test_create_document(self):
        content = b"%PDF-1.4 hello"
        response = self.upload(name="report.pdf", content=content)
        self.assertEqual(response.status_code, 201)

        data = response.data
        self.assertEqual(data["title"], "Report")
        self.assertEqual(data["file_name"], "report.pdf")
        self.assertEqual(data["content_type"], "application/pdf")
        self.assertEqual(data["size"], len(content))
        self.assertEqual(data["checksum"], hashlib.sha256(content).hexdigest())
        self.assertEqual(data["owner"], "editor")
        self.assertTrue(data["url"])

        doc = Document.objects.get(pk=data["id"])
        # stored name is generated, never the user-supplied name
        self.assertTrue(doc.file.name.startswith(f"documents/{self.editor.id}/"))
        self.assertNotIn("report", doc.file.name)
        self.assertTrue(default_storage.exists(doc.file.name))

    def test_unsupported_file_type(self):
        response = self.upload(
            name="evil.exe", content=b"MZ", content_type="application/x-msdownload"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], ErrorCodes.UNSUPPORTED_FILE_TYPE)
        self.assertEqual(Document.objects.count(), 0)

    def test_file_too_large(self):
        with mock.patch("apps.document.service.MAX_DOCUMENT_SIZE", 10):
            response = self.upload(content=b"x" * 11)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], ErrorCodes.FILE_TOO_LARGE)
        self.assertEqual(Document.objects.count(), 0)

    def test_missing_file(self):
        response = self.client.post(
            self.list_url, {"title": "No file"}, format="multipart"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("file", response.data["detail"])

    def test_empty_file(self):
        response = self.upload(content=b"")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Document.objects.count(), 0)


class DocumentReadTests(DocumentAPITestCase):
    def setUp(self):
        super().setUp()
        self.login_as(self.viewer)

    def titles(self, **params):
        response = self.client.get(self.list_url, params)
        self.assertEqual(response.status_code, 200)
        return [item["title"] for item in response.data["results"]]

    def test_retrieve_returns_secure_url(self):
        doc = self.make_document(self.admin)
        response = self.client.get(self.detail_url(doc))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["checksum"], doc.checksum)
        self.assertTrue(response.data["url"])

    def test_retrieve_unknown_document(self):
        response = self.client.get(reverse("documents-detail", kwargs={"pk": 999999}))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["code"], ErrorCodes.NOT_FOUND)

    def test_pagination(self):
        for index in range(25):
            self.make_document(self.admin, title=f"Doc {index}")

        response = self.client.get(self.list_url)
        self.assertEqual(response.data["count"], 25)
        self.assertEqual(len(response.data["results"]), 20)
        self.assertIsNotNone(response.data["next"])

        response = self.client.get(self.list_url, {"page_size": 5})
        self.assertEqual(len(response.data["results"]), 5)

    def test_filters_search_and_ordering(self):
        self.make_document(self.admin, title="Annual Report", content=b"%PDF-1.4 a")
        self.make_document(
            self.editor,
            title="Meeting notes",
            name="notes.txt",
            content=b"n" * 200,
            content_type="text/plain",
        )

        self.assertEqual(self.titles(title="report"), ["Annual Report"])
        self.assertEqual(self.titles(content_type="text/plain"), ["Meeting notes"])
        self.assertEqual(self.titles(owner="EDITOR"), ["Meeting notes"])
        self.assertEqual(self.titles(min_size=100), ["Meeting notes"])
        self.assertEqual(self.titles(max_size=100), ["Annual Report"])
        self.assertEqual(self.titles(search="meeting"), ["Meeting notes"])
        self.assertEqual(self.titles(ordering="-size")[0], "Meeting notes")
        self.assertEqual(self.titles(ordering="size")[0], "Annual Report")


class DocumentUpdateDeleteTests(DocumentAPITestCase):
    def test_update_title_keeps_file(self):
        doc = self.make_document(self.admin)
        file_name = doc.file.name
        self.login_as(self.editor)

        response = self.client.patch(
            self.detail_url(doc), {"title": "Renamed"}, format="multipart"
        )
        self.assertEqual(response.status_code, 200)
        doc.refresh_from_db()
        self.assertEqual(doc.title, "Renamed")
        self.assertEqual(doc.file.name, file_name)

    def test_replace_file_updates_metadata_and_removes_old_file(self):
        doc = self.make_document(self.admin)
        old_name = doc.file.name
        self.login_as(self.editor)

        new_content = b"new text content"
        response = self.client.patch(
            self.detail_url(doc),
            {"file": make_file("new.txt", new_content, "text/plain")},
            format="multipart",
        )
        self.assertEqual(response.status_code, 200)

        doc.refresh_from_db()
        self.assertEqual(doc.file_name, "new.txt")
        self.assertEqual(doc.content_type, "text/plain")
        self.assertEqual(doc.size, len(new_content))
        self.assertEqual(doc.checksum, hashlib.sha256(new_content).hexdigest())
        self.assertFalse(default_storage.exists(old_name))
        self.assertTrue(default_storage.exists(doc.file.name))

    def test_put_is_not_allowed(self):
        doc = self.make_document(self.admin)
        self.login_as(self.admin)
        response = self.client.put(
            self.detail_url(doc), {"title": "x"}, format="multipart"
        )
        self.assertEqual(response.status_code, 405)

    def test_delete_is_soft(self):
        doc = self.make_document(self.editor)
        self.login_as(self.admin)

        response = self.client.delete(self.detail_url(doc))
        self.assertEqual(response.status_code, 204)

        self.assertFalse(Document.objects.filter(pk=doc.pk).exists())
        self.assertTrue(Document.everything.get(pk=doc.pk).is_deleted)
        self.assertTrue(default_storage.exists(doc.file.name))

        self.assertEqual(self.client.get(self.detail_url(doc)).status_code, 404)
        self.assertEqual(self.client.get(self.list_url).data["count"], 0)