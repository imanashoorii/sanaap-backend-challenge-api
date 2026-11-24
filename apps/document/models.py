import os
import uuid

from django.db import models
from django.contrib.auth import get_user_model

from apps.base.models import BaseModel, SoftDelete


def document_upload_path(instance, filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    return f"documents/{instance.owner_id}/{uuid.uuid4().hex}{ext}"


class Document(SoftDelete, BaseModel):
    owner = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        related_name="documents",
        related_query_name="document",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

    file = models.FileField(upload_to=document_upload_path)
    file_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=127)
    size = models.PositiveBigIntegerField(default=0)
    checksum = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["owner", "-created_at"]),
            models.Index(fields=["content_type"]),
        ]

    def __str__(self):
        return self.title