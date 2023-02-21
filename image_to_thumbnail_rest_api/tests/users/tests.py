from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User


class UserTests(APITestCase):
    def setUp(self):
        user = User.objects.create_user(username="some_name", password="some_password")

    def test_login_should_return_200_for_existing_user(self):
        response = self.client.post('/users/login/', {'username': 'some_name', 'password': 'some_password'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_should_return_404_for_not_existing_user(self):
        response = self.client.post('/users/login/', {'username': 'wrong_name', 'password': 'wrong_password'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
