from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from apps.authentication.views import PasswordLoginViewSet, UserViewSet

router = DefaultRouter()
router.register("pass", PasswordLoginViewSet, basename="user-password-authentication")
router.register("users", UserViewSet, basename="users")

urlpatterns = [
    path("refresh/", TokenRefreshView.as_view(), name="refresh-token"),
]
urlpatterns += router.urls