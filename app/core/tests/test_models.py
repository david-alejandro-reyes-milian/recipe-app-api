from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.test import TestCase


class ModelTests(TestCase):
    def test_create_user_with_email_successful(self):
        email = "t@emamil"
        pwd = "pass"
        user: User = get_user_model().objects.create_user(
            email=email,
            password=pwd
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(pwd))
