from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe

from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse("recipe:ingredient-list")


class PublicIngredientsApiTest(TestCase):
    """Test the publicly available ingredients API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required_401(self):
        """Test that login is required to access endpoint"""
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    """Test the private ingredients APIr"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user("test@test.com", "password123")
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients_list(self):
        """Test retrieving a list of ingredients"""
        Ingredient.objects.create(user=self.user, name="Kale")
        Ingredient.objects.create(user=self.user, name="Salt")

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by("-name")
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_t0_user(self):
        """Test that ingredients for the authenticated user are returned"""
        user_2 = get_user_model().objects.create_user("other@test.com", "otherpw")
        Ingredient.objects.create(user=user_2, name="Vinegar")
        ingredient = Ingredient.objects.create(user=self.user, name="Tumeric")

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], ingredient.name)

    def test_create_ingredient_successful(self):
        """Test create a new ingredient"""
        payload = {"name": "Cabbage"}
        self.client.post(INGREDIENTS_URL, payload)

        exists = Ingredient.objects.filter(
            user=self.user, name=payload["name"]
        ).exists()

        self.assertTrue(exists)

    def test_create_ingredients_invalid(self):
        """Test creating invalid ingredient fails"""
        payload = {"name": ""}
        res = self.client.post(INGREDIENTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_ingredients_assigned_to_recipes(self):
        """Test filtering ingredients by those assigned to recipes"""
        ingredient_1 = Ingredient.objects.create(user=self.user, name="Apples")
        ingredient_2 = Ingredient.objects.create(user=self.user, name="Turkey")
        recipe = Recipe.objects.create(
            user=self.user,
            title="Apple Crumble",
            time_minutes=35,
            price=5.00,
        )
        recipe.ingredients.add(ingredient_1)

        res = self.client.get(INGREDIENTS_URL, {"assigned_only": 1})

        serializer_1 = IngredientSerializer(ingredient_1)
        serializer_2 = IngredientSerializer(ingredient_2)

        self.assertIn(serializer_1.data, res.data)
        self.assertNotIn(serializer_2.data, res.data)

    def test_retrieve_ingredients_assigned_unique(self):
        """Test filtering ingredients by assigned returns unqiue items"""
        ingredient = Ingredient.objects.create(user=self.user, name="Eggs")
        Ingredient.objects.create(user=self.user, name="Cheese")

        recipe_1 = Recipe.objects.create(
            user=self.user,
            title="Eggs Benedict",
            time_minutes=30,
            price=12.00,
        )
        recipe_1.ingredients.add(ingredient)

        recipe_2 = Recipe.objects.create(
            user=self.user,
            title="Scrambled Eggs",
            time_minutes=3,
            price=2.00,
        )
        recipe_2.ingredients.add(ingredient)

        res = self.client.get(INGREDIENTS_URL, {"assigned_only": 1})

        self.assertEqual(len(res.data), 1)
