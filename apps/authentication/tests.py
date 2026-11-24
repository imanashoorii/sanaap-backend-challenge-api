from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.authentication.choices import UserRoleChoices
from apps.base.testing import BaseAPITestCase, TEST_PASSWORD
from general.enum import ErrorCodes

User = get_user_model()


class LoginTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.login_url = reverse("user-password-authentication-login")
        self.me_url = reverse("user-password-authentication-me")

    def login(self, identifier, password=TEST_PASSWORD):
        return self.client.post(
            self.login_url,
            {"username": identifier, "password": password},
            format="json",
        )

    def test_login_with_username(self):
        response = self.login("viewer")
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_with_email_is_case_insensitive(self):
        response = self.login("VIEWER@Example.com")
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)

    def test_wrong_password(self):
        response = self.login("viewer", "wrong-password")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["code"], ErrorCodes.INVALID_CREDENTIALS)

    def test_unknown_user_gets_same_error_as_wrong_password(self):
        wrong_password = self.login("viewer", "wrong-password")
        unknown_user = self.login("nobody", "wrong-password")
        self.assertEqual(unknown_user.status_code, 401)
        self.assertEqual(unknown_user.data, wrong_password.data)

    def test_inactive_user_cannot_login(self):
        User.objects.filter(username="viewer").update(is_active=False)
        response = self.login("viewer")
        self.assertEqual(response.status_code, 401)

    def test_login_is_throttled(self):
        for _ in range(10):
            self.login("viewer", "wrong-password")
        response = self.login("viewer", "wrong-password")
        self.assertEqual(response.status_code, 429)

    def test_refresh_token(self):
        refresh = self.login("viewer").data["refresh"]
        response = self.client.post(
            reverse("refresh-token"), {"refresh": refresh}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)

    def test_me_requires_authentication(self):
        self.assertEqual(self.client.get(self.me_url).status_code, 401)

    def test_me_returns_current_user(self):
        self.login_as(self.editor)
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], "editor")
        self.assertEqual(response.data["role"], UserRoleChoices.EDITOR)

    def test_anonymous_cannot_delete_users(self):
        # regression: login viewset must not expose model-viewset routes
        response = self.client.delete(f"/v1/auth/pass/{self.viewer.pk}/")
        self.assertIn(response.status_code, (404, 405))
        self.assertTrue(User.objects.filter(pk=self.viewer.pk).exists())


class UserManagementTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.list_url = reverse("users-list")

    def detail_url(self, user):
        return reverse("users-detail", kwargs={"pk": user.pk})

    def payload(self, **overrides):
        data = {
            "username": "newbie",
            "email": "New@Example.com",
            "password": TEST_PASSWORD,
            "role": UserRoleChoices.EDITOR,
        }
        data.update(overrides)
        return data

    def test_only_admin_can_list_users(self):
        self.assertEqual(self.client.get(self.list_url).status_code, 401)
        for user in (self.viewer, self.editor):
            self.login_as(user)
            self.assertEqual(self.client.get(self.list_url).status_code, 403)
        self.login_as(self.admin)
        self.assertEqual(self.client.get(self.list_url).status_code, 200)

    def test_admin_creates_user(self):
        self.login_as(self.admin)
        response = self.client.post(self.list_url, self.payload(), format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["email"], "new@example.com")
        self.assertEqual(response.data["role"], UserRoleChoices.EDITOR)
        self.assertNotIn("password", response.data)

        # the new user can log in with email
        self.client.force_authenticate(user=None)
        login = self.client.post(
            reverse("user-password-authentication-login"),
            {"username": "new@example.com", "password": TEST_PASSWORD},
            format="json",
        )
        self.assertEqual(login.status_code, 200)

    def test_non_admin_cannot_create_user(self):
        for user in (self.viewer, self.editor):
            self.login_as(user)
            response = self.client.post(self.list_url, self.payload(), format="json")
            self.assertEqual(response.status_code, 403)
        self.assertFalse(User.objects.filter(username="newbie").exists())

    def test_duplicate_username(self):
        self.login_as(self.admin)
        response = self.client.post(
            self.list_url, self.payload(username="viewer"), format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("username", response.data["detail"])

    def test_duplicate_email_is_case_insensitive(self):
        self.login_as(self.admin)
        response = self.client.post(
            self.list_url, self.payload(email="VIEWER@example.com"), format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.data["detail"])

    def test_weak_password(self):
        self.login_as(self.admin)
        response = self.client.post(
            self.list_url, self.payload(password="12345678"), format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("password", response.data["detail"])

    def test_admin_changes_role(self):
        self.login_as(self.admin)
        response = self.client.patch(
            self.detail_url(self.viewer),
            {"role": UserRoleChoices.EDITOR},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.viewer.refresh_from_db()
        self.assertEqual(self.viewer.role, UserRoleChoices.EDITOR)

    def test_admin_cannot_change_own_role(self):
        self.login_as(self.admin)
        response = self.client.patch(
            self.detail_url(self.admin),
            {"role": UserRoleChoices.VIEWER},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], ErrorCodes.OBJ_NOT_EDITABLE)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.role, UserRoleChoices.ADMIN)

    def test_delete_is_not_allowed(self):
        self.login_as(self.admin)
        response = self.client.delete(self.detail_url(self.viewer))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(User.objects.filter(pk=self.viewer.pk).exists())