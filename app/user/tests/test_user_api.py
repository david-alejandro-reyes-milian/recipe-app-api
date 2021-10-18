from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from core.models import User as UserModel

CREATE_USER_URL = reverse('user:create')
ME_URL = reverse('user:me')
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

    def test_retrieve_user_unauthorized(self):
        res: Response = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    def setUp(self) -> None:
        self.user = create_user(
            email="email@email.com",
            password="password",
            name="testuser",
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_user(self):
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(res.data, {
            'name': self.user.name,
            'email': self.user.email
        })

    def test_post_me_not_allowed(self):
        res = self.client.post(ME_URL, {})
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        payload = {
            'email': 'email@email.com',
            'password': 'newwpassword',
            'name': 'newname'
        }
        res = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()

        self.assertEqual(self.user.name, payload['name'])
        self.assertEqual(self.user.email, payload['email'])
        self.assertTrue(self.user.check_password(payload['password']))

        self.assertEqual(res.status_code, status.HTTP_200_OK)
