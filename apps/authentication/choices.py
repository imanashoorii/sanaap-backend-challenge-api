from django.db import models


class UserRoleChoices(models.IntegerChoices):
    ADMIN = 1, "ADMIN"
    EDITOR = 2, "EDITOR"
    VIEWER = 3, "VIEWER"