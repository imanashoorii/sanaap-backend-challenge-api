from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models

from apps.base.models import BaseModel
from apps.authentication.choices import UserRoleChoices

class CustomUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", UserRoleChoices.ADMIN)
        return super().create_superuser(username, email, password, **extra_fields)

class User(AbstractUser, BaseModel):
    role = models.IntegerField(
        choices=UserRoleChoices.choices,
        default=UserRoleChoices.VIEWER,
    )
    email = models.EmailField(unique=True)

    objects = CustomUserManager()

    @property
    def is_admin_role(self) -> bool:
        return self.role == UserRoleChoices.ADMIN

    @property
    def is_editor_role(self) -> bool:
        return self.role == UserRoleChoices.EDITOR

    @property
    def is_viewer_role(self) -> bool:
        return self.role == UserRoleChoices.VIEWER