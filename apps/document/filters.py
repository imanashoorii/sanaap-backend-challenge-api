import django_filters

from apps.document.models import Document


class DocumentFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr="icontains")
    file_name = django_filters.CharFilter(lookup_expr="icontains")
    owner = django_filters.CharFilter(field_name="owner__username", lookup_expr="iexact")
    min_size = django_filters.NumberFilter(field_name="size", lookup_expr="gte")
    max_size = django_filters.NumberFilter(field_name="size", lookup_expr="lte")
    created_from = django_filters.IsoDateTimeFilter(
        field_name="created_at", lookup_expr="gte"
    )
    created_to = django_filters.IsoDateTimeFilter(
        field_name="created_at", lookup_expr="lte"
    )

    class Meta:
        model = Document
        fields = ("content_type",)