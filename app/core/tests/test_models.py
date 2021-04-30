from django.test import TestCase
from django.contrib.auth import get_user_model


class ModelTests(TestCase):
    def test_create_user_with_email_successful(self):
        """Test creating new user with email is successful"""
        email = "test@test.com"
        password = "Password123!"
        user = get_user_model().objects.create_user(email, password)

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test the email for a new user is normalized"""
        email = "test@TESTEMAIL.com"
        user = get_user_model().objects.create_user(email, "Password123!")

        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        """Test creating user with no email raises error"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, "Password123!")

    def test_create_new_superuser(self):
        """Test creating a new superuser"""
        user = get_user_model().objects.create_superuser("test@test.com", "password123")

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
