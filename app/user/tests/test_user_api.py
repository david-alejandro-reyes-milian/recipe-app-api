from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from core.models import User as UserModel

CREATE_USER_URL = reverse('user:create')
CREATE_TOKEN_URL = reverse('user:token')
User: UserModel = get_user_model()


def create_user(**param) -> User:
    return User.objects.create_user(**param)


class PublicUserApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_create_valid_user_success(self):
        payload = {
            'email': 'test@gmail.com',
            'password': 'longpass123',
            'name': 'Test Name'
        }
        res: Response = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(**res.data)

        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_user_exists(self):
        payload = {
            'email': 'test@gmail.com',
            'password': 'test@gmail.com'
        }
        res: Response = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        payload = {
            'email': 'test@gmail.com',
            'password': 'pw',
            'name': 'Test'
        }
        res: Response = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        exists = User.objects.filter(email=payload['email']).exists()
        self.assertFalse(exists)

    def test_create_token_for_user(self):
        payload = {
            'email': 'test@gmail.com',
            'password': 'test@gmail.com'
        }
        create_user(**payload)

        res: Response = self.client.post(CREATE_TOKEN_URL, payload)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        create_user(email="test@gmail.com", password="mypass")
        payload = {
            'email': 'test@gmail.com',
            'password': 'wrong pass'
        }

        res: Response = self.client.post(CREATE_TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        payload = {
            'email': 'test@gmail.com',
            'password': 'mypassword'
        }

        res: Response = self.client.post(CREATE_TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field(self):
        res: Response = self.client.post(
            CREATE_TOKEN_URL,
            {'email': 'one', 'password': ''}
        )
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
