from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag
from recipe.serializers import TagSerializer
from recipe.tests.test_recipe_api import sample_tag, sample_recipe

TAGS_URL = reverse('recipe:tag-list')


class PublicTagsApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_login_required(self):
        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            'a@gmmail.com',
            'mypassword'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        Tag.objects.create(user=self.user, name='TagA')
        Tag.objects.create(user=self.user, name='TagB')

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        user2 = get_user_model().objects.create_user(
            'ab@gmmail.com',
            'mypassword'
        )

        Tag.objects.create(user=user2, name='TagA')
        tag = Tag.objects.create(user=self.user, name='TagB')

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)

    def test_create_tag_successful(self):
        payload = {'name': "Tag"}
        res = self.client.post(TAGS_URL, payload)

        exist = Tag.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()
        self.assertTrue(exist)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_create_invalid(self):
        payload = {'name': ''}
        res = self.client.post(TAGS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_tags_assigned_to_recipe(self):
        t1 = sample_tag(self.user, 't1')
        t2 = sample_tag(self.user, 't2')
        r1 = sample_recipe(self.user)
        r1.tags.add(t1)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        serializer1 = TagSerializer(t1)
        serializer2 = TagSerializer(t2)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_retrieve_tags_assigned_unique(self):
        t1 = sample_tag(self.user, 't1')
        sample_tag(self.user, 't2')

        r1 = sample_recipe(self.user)
        r2 = sample_recipe(self.user)
        r1.tags.add(t1)
        r2.tags.add(t1)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
