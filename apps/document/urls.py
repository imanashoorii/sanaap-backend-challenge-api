from rest_framework.routers import DefaultRouter

from apps.document.views import DocumentViewSet

router = DefaultRouter()
router.register("docs", DocumentViewSet, basename="documents")
urlpatterns = []
urlpatterns += router.urls
