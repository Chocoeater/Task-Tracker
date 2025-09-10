from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

User = get_user_model()


class Task(models.Model):

    class Meta:
        verbose_name = "задача"
        verbose_name_plural = "задачи"

    class Status(models.TextChoices):
        CREATED = "created", "создана"
        IN_PROGRESS = "in_progress", "в работе"
        DONE = "done", "исполнена"
        NOT_DONE = "not_done", "не исполнена"
        BLOCKED = "blocked", "отозвана"

    class Priority(models.TextChoices):
        LOW = "low", "низкий"
        MEDIUM = "medium", "средний"
        HIGH = "high", "высокий"

    executor = models.ForeignKey(
        User,
        related_name="executed_tasks",
        verbose_name="исполнитель",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        db_index=True,
    )
    author = models.ForeignKey(
        User,
        related_name="authored_tasks",
        verbose_name="автор",
        on_delete=models.SET_NULL,
        null=True,
    )
    name = models.CharField(max_length=150, verbose_name="имя задачи")
    description = models.TextField(verbose_name="описание задачи")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.CREATED, db_index=True
    )
    priority = models.CharField(
        max_length=20, choices=Priority.choices, default=Priority.MEDIUM
    )
    deadline = models.DateTimeField(
        null=True, blank=True, verbose_name="срок выполнения", db_index=True
    )
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="subtasks", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()

        if self.parent and self.parent_id == self.id:
            raise ValidationError("Задача не может быть родителем для самой себя")

    def save(self, *args, **kwargs):
        if self.status == self.Status.DONE and not self.completed_at:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)
