from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, inline_serializer

from rest_framework import mixins, viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.base.mixins import BaseMixin
from apps.authentication.permissions import IsAdminRole
from apps.authentication.serializers import (
    UserSerializer,
    PasswordLoginSerializer,
    CreateUserSerializer,
    UpdateUserSerializer,
)
from apps.authentication.throttling import AuthAPIRateThrottle

User = get_user_model()


class PasswordLoginViewSet(BaseMixin, viewsets.GenericViewSet):
    serializer_classes_by_action = {
        "login": PasswordLoginSerializer,
        "me": UserSerializer,
    }

    permission_classes_by_action = {
        "login": (AllowAny,),
        "me": (IsAuthenticated,),
    }

    throttle_classes_by_action = {
        "login": AuthAPIRateThrottle,
    }


    @extend_schema(
        responses=inline_serializer(
            "TokenPair",
            {"access": serializers.CharField(), "refresh": serializers.CharField()},
        )
    )
    @action(detail=False, methods=["post"], url_path="login")
    def login(self, request):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        return Response(data=serializer.validated_data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class UserViewSet(
    BaseMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = User.objects.all().order_by("-created_at")
    http_method_names = ("get", "post", "patch", "head", "options")

    serializer_classes_by_action = {
        "list": UserSerializer,
        "retrieve": UserSerializer,
        "create": CreateUserSerializer,
        "partial_update": UpdateUserSerializer,
    }
    permission_classes_by_action = {
        "list": (IsAdminRole,),
        "retrieve": (IsAdminRole,),
        "create": (IsAdminRole,),
        "partial_update": (IsAdminRole,),
    }