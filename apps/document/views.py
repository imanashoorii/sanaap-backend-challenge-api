from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.base.mixins import BaseMixin
from apps.authentication.permissions import (
    IsAdminRole,
    IsAdminOrEditorRole,
    IsAnyRole,
)
from apps.document.filters import DocumentFilter
from apps.document.models import Document
from apps.document.pagination import DocumentPagination
from apps.document.serializers import (
    DocumentListSerializer,
    DocumentRetrieveSerializer,
    CreateDocumentSerializer,
    UpdateDocumentSerializer,
)


class DocumentViewSet(
    BaseMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    parser_classes = (MultiPartParser, FormParser)
    queryset = Document.objects.select_related("owner")
    http_method_names = ("get", "post", "patch", "delete", "head", "options")

    pagination_class = DocumentPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = DocumentFilter
    search_fields = ("title", "description", "file_name")
    ordering_fields = ("created_at", "size", "title")

    serializer_classes_by_action = {
        "list": DocumentListSerializer,
        "retrieve": DocumentRetrieveSerializer,
        "create": CreateDocumentSerializer,
        "partial_update": UpdateDocumentSerializer,
    }
    permission_classes_by_action = {
        "list": (IsAnyRole,),
        "retrieve": (IsAnyRole,),
        "create": (IsAdminOrEditorRole,),
        "partial_update": (IsAdminOrEditorRole,),
        "destroy": (IsAdminRole,),
    }

    def perform_destroy(self, instance):
        instance.soft_delete()
