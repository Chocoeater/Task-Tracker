from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

User = get_user_model()
from tasks.models import Task

class UsersTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create(
            email="admin@example.com", password="password123", is_superuser=True, is_active=True
        )
        self.manager = User.objects.create(
            email="manager@example.com", password="password123", role="manager", is_active=True
        )
        self.dev = User.objects.create(
            email="dev@example.com", password="password123", role="developer", is_active=True
        )

        Task.objects.create(
            name="Dev Task", description="Task 1", author=self.manager, executor=self.dev, status="in_progress"
        )

    def test_me_get(self):
        self.client.force_authenticate(user=self.dev)
        url = reverse("users:users-me")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.dev.email)

    def test_me_patch(self):
        self.client.force_authenticate(user=self.dev)
        url = reverse("users:users-me")
        data = {"first_name": "NewName"}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.dev.refresh_from_db()
        self.assertEqual(self.dev.first_name, "NewName")

    def test_busy_executors_for_manager(self):
        self.client.force_authenticate(user=self.manager)
        url = reverse("users:users-busy-executors")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["email"], self.dev.email)

    def test_busy_executors_for_dev_forbidden(self):
        self.client.force_authenticate(user=self.dev)
        url = reverse("users:users-busy-executors")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_users_for_manager(self):
        self.client.force_authenticate(user=self.manager)
        url = reverse("users:users-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_users_for_dev_forbidden(self):
        self.client.force_authenticate(user=self.dev)
        url = reverse("users:users-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_user_by_admin(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse("users:users-list")
        data = {
            "email": "newuser@example.com",
            "password": "newpass123",
            "first_name": "First",
            "last_name": "Last",
            "role": "developer"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="newuser@example.com").exists())

    def test_create_user_by_manager_forbidden(self):
        self.client.force_authenticate(user=self.manager)
        url = reverse("users:users-list")
        data = {"email": "hack@example.com", "password": "pass"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
