from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.test import TestCase

user_model: User = get_user_model()


class ModelTests(TestCase):
    def test_create_user_with_email_successful(self):
        email = "t@emamil"
        pwd = "pass"
        user: User = user_model.objects.create_user(
            email=email,
            password=pwd
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(pwd))

    def test_new_user_normalize(self):
        email = 'test@Loasdsd.com'
        user = user_model.objects.create_user(email, 'pass')

        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        with self.assertRaises(ValueError):
            user_model.objects.create_user(None, 'pass')

    def test_new_user_invalid_pass(self):
        with self.assertRaises(ValueError):
            user_model.objects.create_user(email="email@a.c", password=None)

    def test_create_new_superuser(self):
        email = "t@emamil"
        pwd = "pass"
        user: User = user_model.objects.create_superuser(
            email=email,
            password=pwd
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
