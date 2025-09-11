from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from tasks.models import Task

User = get_user_model()


class TasksTests(APITestCase):
    def setUp(self):
        self.dev = User.objects.create(
            email="dev@test.com", password="test1234", role="developer", is_active=True
        )
        self.other_dev = User.objects.create(
            email="dev2@test.com", password="test1234", role="developer", is_active=True
        )
        self.manager = User.objects.create(
            email="manager@test.com",
            password="test1234",
            role="manager",
            is_active=True,
        )

        self.task_free = Task.objects.create(
            name="Test free task",
            description="test",
            deadline="2025-12-31T23:59:59+03:00",
        )
        self.task_taken = Task.objects.create(
            name="Test task",
            description="test",
            deadline="2025-12-31T23:59:59+03:00",
            executor=self.dev,
            status="in_progress",
            author=self.manager,
        )

        self.list_url = reverse("tasks:tasks-list")
        self.assign_url = reverse("tasks:tasks-assign", args=[self.task_free.id])
        self.release_url = reverse("tasks:tasks-release", args=[self.task_taken.id])
        self.complete_url = reverse("tasks:tasks-complete", args=[self.task_taken.id])
        self.free_url = reverse("tasks:tasks-free")
        self.important_url = reverse("tasks:tasks-important")

    def test_list_anon(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_manager(self):
        self.client.force_authenticate(self.manager)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_list_dev(self):
        self.client.force_authenticate(self.dev)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_assign_manager_can_assign_anyone(self):
        self.client.force_authenticate(self.manager)
        response = self.client.post(self.assign_url, {"executor_id": self.other_dev.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task_free.refresh_from_db()
        self.assertEqual(self.task_free.executor, self.other_dev)

    def test_assign_dev_can_assign_only_self(self):
        self.client.force_authenticate(self.dev)
        response = self.client.post(self.assign_url, {"executor_id": self.other_dev.id})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_release_only_manager_or_admin(self):
        self.client.force_authenticate(self.dev)
        response = self.client.post(self.release_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.manager)
        response = self.client.post(self.release_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_complete_by_executor(self):
        self.client.force_authenticate(self.dev)
        response = self.client.post(self.complete_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task_taken.refresh_from_db()
        self.assertEqual(self.task_taken.status, "done")

    def test_free_tasks(self):
        self.client.force_authenticate(self.dev)
        response = self.client.get(self.free_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_important_tasks_only_for_manager(self):
        self.client.force_authenticate(self.dev)
        response = self.client.get(self.important_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.manager)
        response = self.client.get(self.important_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
