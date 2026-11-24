from rest_framework import serializers

from apps.document.models import Document
from apps.document.service import DocumentServices


class DocumentListSerializer(serializers.ModelSerializer):
    owner = serializers.CharField(source="owner.username", read_only=True)

    class Meta:
        model = Document
        fields = (
            "id",
            "title",
            "file_name",
            "content_type",
            "size",
            "owner",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class DocumentRetrieveSerializer(DocumentListSerializer):
    url = serializers.SerializerMethodField()

    class Meta(DocumentListSerializer.Meta):
        fields = DocumentListSerializer.Meta.fields + (
            "description",
            "checksum",
            "url",
        )
        read_only_fields = fields

    def get_url(self, obj) -> str:
        return obj.file.url


class CreateDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ("title", "description", "file")

    def validate_file(self, file):
        DocumentServices.validate_file(file)
        return file

    def create(self, validated_data):
        metadata = DocumentServices.get_file_metadata(validated_data["file"])
        return Document.objects.create(
            owner=self.context["request"].user, **validated_data, **metadata
        )

    def to_representation(self, instance):
        return DocumentRetrieveSerializer(instance, context=self.context).data


class UpdateDocumentSerializer(CreateDocumentSerializer):
    def update(self, instance, validated_data):
        new_file = validated_data.get("file")
        old_name = instance.file.name if new_file else None

        if new_file:
            validated_data.update(DocumentServices.get_file_metadata(new_file))

        instance = super().update(instance, validated_data)

        if old_name:
            instance.file.storage.delete(old_name)
        return instance