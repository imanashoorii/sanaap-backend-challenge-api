from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth import password_validation
from django.contrib.auth.models import update_last_login
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import serializers
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from general.enum import UserMessages
from general.utils import get_tokens_for_user
from apps.base.exceptions import ForbiddenUpdate
from apps.authentication.exceptions import InvalidCredentials
from apps.authentication.service import UserServices

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "role",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class PasswordLoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        status, username = UserServices.retrieve_user_by_identifier(username)
        if not status:
            raise InvalidCredentials()

        user = authenticate(username=username, password=password)

        if not user or not api_settings.USER_AUTHENTICATION_RULE(user):
            raise InvalidCredentials()

        access, refresh = get_tokens_for_user(user)
        update_last_login(None, user)
        return {"access": access, "refresh": refresh}


class CreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "role")
        extra_kwargs = {"email": {"required": True}}

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(UserMessages.USERNAME_TAKEN)
        return value

    def validate_email(self, value):
        value = value.lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(UserMessages.EMAIL_TAKEN)
        return value

    def validate_password(self, value):
        try:
            password_validation.validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

    def to_representation(self, instance):
        return UserSerializer(instance).data


class UpdateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("role", "is_active")

    def validate(self, attrs):
        if self.instance == self.context["request"].user:
            raise ForbiddenUpdate()
        return attrs

    def to_representation(self, instance):
        return UserSerializer(instance).data