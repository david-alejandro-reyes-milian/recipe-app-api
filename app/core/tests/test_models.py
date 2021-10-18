from django.contrib.auth import get_user_model
from core.models import User as UserModel
from django.test import TestCase

from core import models

User: UserModel = get_user_model()


def sample_user(email="testemail@gmail.com", pwd="mypassword") -> UserModel:
    return User.objects.create_user(
        email=email,
        password=pwd
    )


class ModelTests(TestCase):
    def test_create_user_with_email_successful(self):
        email = "t@emamil"
        pwd = "pass"
        user: UserModel = User.objects.create_user(
            email=email,
            password=pwd
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(pwd))

    def test_new_user_normalize(self):
        email = 'test@Loasdsd.com'
        user = User.objects.create_user(email, 'pass')

        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(None, 'pass')

    def test_new_user_invalid_pass(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email="email@a.c", password=None)

    def test_create_new_superuser(self):
        email = "t@emamil"
        pwd = "pass"
        user: UserModel = User.objects.create_superuser(
            email=email,
            password=pwd
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_tag_str(self):
        tag = models.Tag.objects.create(
            user=sample_user(),
            name='Vegan'
        )

        self.assertEqual(str(tag), tag.name)

    def test_ingredient_str(self):
        ingredient = models.Ingredient.objects.create(
            user=sample_user(),
            name='Kardamomo'
        )

        self.assertEqual(str(ingredient), ingredient.name)
