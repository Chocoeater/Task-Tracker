from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

User = get_user_model()


class Task(models.Model):
    """
    Модель задачи для системы управления задачами.

    Описывает задачу, её автора, исполнителя, статус, приоритет и сроки выполнения.
    Поддерживает иерархическую структуру через связь с родительской задачей.

    Attributes
    ----------
    executor : User, optional
        Пользователь, назначенный исполнителем задачи.
    author : User, optional
        Пользователь, создавший задачу.
    name : str
        Название задачи (макс. 150 символов).
    description : str
        Подробное описание задачи.
    status : str
        Текущий статус задачи. Возможные значения:

        - ``created`` — создана
        - ``in_progress`` — в работе
        - ``done`` — исполнена
        - ``not_done`` — не исполнена
        - ``blocked`` — отозвана
    priority : str
        Приоритет задачи. Возможные значения:

        - ``low`` — низкий
        - ``medium`` — средний
        - ``high`` — высокий
    deadline : datetime, optional
        Дедлайн выполнения задачи.
    parent : Task, optional
        Родительская задача (для организации подзадач).
    created_at : datetime
        Дата и время создания задачи (устанавливается автоматически).
    updated_at : datetime
        Дата и время последнего обновления (устанавливается автоматически).
    completed_at : datetime, optional
        Дата и время завершения задачи (устанавливается автоматически при смене
        статуса на ``done``).

    Methods
    -------
    __str__()
        Возвращает название задачи.
    clean()
        Проверяет корректность данных (например, что задача не может быть
        родителем самой себе).
    save(*args, **kwargs)
        Сохраняет задачу и при необходимости автоматически выставляет время
        завершения.
    """
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
        """
        Возвращает строковое представление задачи.

        Returns
        -------
        str
            Название задачи.
        """
        return self.name

    def clean(self):
        """
        Проверяет корректность данных модели.

        Raises
        ------
        ValidationError
            Если задача указана как родитель самой себе.
        """
        super().clean()

        if self.parent and self.parent_id == self.id:
            raise ValidationError("Задача не может быть родителем для самой себя")

    def save(self, *args, **kwargs):
        """
        Сохраняет задачу в базу данных.

        Если статус задачи установлен в ``done`` и поле ``completed_at``
        ещё не заполнено, автоматически выставляется текущая дата и время.

        Parameters
        ----------
        *args : list
            Позиционные аргументы для метода ``save``.
        **kwargs : dict
            Именованные аргументы для метода ``save``.
        """
        if self.status == self.Status.DONE and not self.completed_at:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)
