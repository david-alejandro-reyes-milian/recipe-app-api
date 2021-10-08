from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import reverse
from rest_framework.reverse import reverse

from core.models import User

User: User = get_user_model()


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
