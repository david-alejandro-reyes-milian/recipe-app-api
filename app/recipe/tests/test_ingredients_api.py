from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient
from recipe.serializers import IngredientSerializer
from recipe.tests.test_recipe_api import sample_ingredient, sample_recipe

INGREDIENT_URL = reverse('recipe:ingredient-list')


class PublicIngredientApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_login_required(self):
        res = self.client.get(INGREDIENT_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientApiTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            'a@gmmail.com',
            'mypassword'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients_list(self):
        Ingredient.objects.create(name="I1", user=self.user)

        res = self.client.get(INGREDIENT_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        user2 = get_user_model().objects.create_user(
            'aa@gmmail.com',
            'mypassword'
        )
        Ingredient.objects.create(name="I1", user=user2)
        ingredient = Ingredient.objects.create(name="I2", user=self.user)

        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)

    def test_create_ingredient_successful(self):
        payload = {'name': "I1"}
        res = self.client.post(INGREDIENT_URL, payload)
        exists = Ingredient.objects.all().filter(
            name=payload['name'],
            user=self.user
        ).exists()
        self.assertTrue(exists)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_create_ingredient_fails(self):
        payload = {'name': ""}
        res = self.client.post(INGREDIENT_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_ingredients_assigned_to_recipe(self):
        a = sample_ingredient(self.user, 't1')
        b = sample_ingredient(self.user, 't2')
        r1 = sample_recipe(self.user)
        r1.ingredients.add(a)

        res = self.client.get(INGREDIENT_URL, {'assigned_only': 1})

        serializer1 = IngredientSerializer(a)
        serializer2 = IngredientSerializer(b)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_retrieve_ingredients_assigned_unique(self):
        a = sample_ingredient(self.user, 't1')
        sample_ingredient(self.user, 't2')

        r1 = sample_recipe(self.user)
        sample_recipe(self.user)
        r1.ingredients.add(a)

        res = self.client.get(INGREDIENT_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
