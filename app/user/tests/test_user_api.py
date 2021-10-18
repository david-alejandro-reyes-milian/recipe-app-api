from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from core.models import User as UserModel

CREATE_URL = reverse('user:create')
User: UserModel = get_user_model()


def create_user(**param) -> User:
    return User.objects.create(**param)


class PublicUserApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_create_valid_user_success(self):
        payload = {
            'email': 'test@gmail.com',
            'password': 'longpass123',
            'name': 'Test Name'
        }
        res: Response = self.client.post(CREATE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(**res.data)

        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_user_exists(self):
        payload = {
            'email': 'test@gmail.com',
            'password': 'test@gmail.com'
        }
        res: Response = self.client.post(CREATE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        payload = {
            'email': 'test@gmail.com',
            'password': 'pw',
            'name': 'Test'
        }
        res: Response = self.client.post(CREATE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        exists = User.objects.filter(email=payload['email']).exists()
        self.assertFalse(exists)
