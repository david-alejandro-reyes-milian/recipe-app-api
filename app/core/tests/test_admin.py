from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from core.models import User as UserModel

User: UserModel = get_user_model()


class AdminSiteTests(TestCase):

    def setUp(self) -> None:
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            email="superuser@google.com",
            password="password",
        )

        self.client.force_login(self.admin_user)

        self.user = User.objects.create_user(
            email="user@google.com",
            password="password",
        )

    def test_users_listed(self):
        url = reverse('admin:core_user_changelist')
        res = self.client.get(url)

        self.assertContains(res, self.user.name)
        self.assertContains(res, self.user.name)

    def test_user_change_page(self):
        url = reverse('admin:core_user_change', args=[self.user.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)

    def test_create_user_page(self):
        url = reverse('admin:core_user_add')
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)
