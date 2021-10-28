import os.path
import tempfile
from unittest.mock import patch

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core import models
from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPE_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    return reverse('recipe:recipe-detail', args=[recipe_id])


def image_upload_url(recipe_id):
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


def sample_tag(user, name="Main course"):
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name="Cinnamon"):
    return Ingredient.objects.create(user=user, name=name)


def sample_recipe(user, **params):
    defaults = {
        'title': 'Sample',
        'time_minutes': 10,
        'price': 5.00
    }
    defaults.update(params)
    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_login_required(self):
        res = self.client.get(RECIPE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            'a@gmmail.com',
            'mypassword'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes_list(self):
        sample_recipe(self.user)
        sample_recipe(self.user)

        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.all().filter(user=self.user).order_by('-title')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        user2 = get_user_model().objects.create_user(
            'aa@gmmail.com',
            'mypassword'
        )
        sample_recipe(user2)
        recipe = sample_recipe(self.user)

        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], recipe.id)

    def test_create_recipe_fails(self):
        payload = {'title': ""}
        res = self.client.post(RECIPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_view_recipe_detail(self):
        recipe = sample_recipe(self.user)
        recipe.tags.add(sample_tag(self.user))
        recipe.ingredients.add(sample_ingredient(self.user))

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe_successful(self):
        payload = {'title': "I1", 'price': 5.00, 'time_minutes': 10}
        res = self.client.post(RECIPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        tag1 = sample_tag(self.user, 'tag1')
        tag2 = sample_tag(self.user, 'tag2')

        payload = {
            'title': "I1",
            'price': 5.00,
            'time_minutes': 10,
            'tags': [tag1.id, tag2.id],
        }

        res = self.client.post(RECIPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_with_ingredients(self):
        i1 = sample_ingredient(self.user, 'i1')
        i2 = sample_ingredient(self.user, 'i2')

        payload = {
            'title': "I1",
            'price': 5.00,
            'time_minutes': 10,
            'ingredients': [i1.id, i2.id],
        }

        res = self.client.post(RECIPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(i1, ingredients)
        self.assertIn(i2, ingredients)

    def test_recipe_partial_update(self):
        recipe = sample_recipe(self.user)
        recipe.tags.add(sample_tag(self.user))
        new_tag = sample_tag(user=self.user, name='new_tag')

        payload = {
            'title': 'Chicken Tikka',
            'tags': (new_tag.id,)
        }

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)
        recipe.refresh_from_db()

        self.assertEqual(res.data['title'], recipe.title)
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 1)
        self.assertIn(new_tag, tags)

    def test_recipe_full_update(self):
        recipe = sample_recipe(self.user)
        payload = {
            'title': 'New Title',
            'time_minutes': 2,
            'price': 2.00
        }

        url = detail_url(recipe.id)
        res = self.client.put(url, payload)
        recipe.refresh_from_db()

        self.assertEqual(res.data['title'], recipe.title)
        self.assertEqual(res.data['time_minutes'], recipe.time_minutes)
        self.assertEqual(res.data['price'], str(recipe.price))
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 0)

    @patch('uuid.uuid4')
    def test_recipe_filename_uuid(self, mock_uuid):
        uuid = 'mock_uuid'
        mock_uuid.return_value = uuid

        file_path = models.recipe_image_file_path(None, 'myimage.jpg')
        exp_path = f'uploads/recipe/{uuid}.jpg'
        self.assertEqual(file_path, exp_path)


class RecipeImageUploadTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'a@gmmail.com',
            'mypassword'
        )
        self.client.force_authenticate(self.user)
        self.recipe = sample_recipe(self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image_to_recipe(self):
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            ntf.seek(0)
            res = self.client.post(url, {'image': ntf}, format='multipart')
        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        url = image_upload_url(self.recipe.id)
        res = self.client.post(url, {'image': 'noimage'}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
