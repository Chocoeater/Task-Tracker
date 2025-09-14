from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework.fields import SerializerMethodField
from rest_framework import serializers

from tasks import validators
from tasks.models import Task

User = get_user_model()


class TaskSubtaskSerializer(serializers.ModelSerializer):
    """
    Сериализатор подзадач.

    Используется для вложенного отображения информации о подзадачах.

    Fields
    ------
    id : int
        Идентификатор подзадачи.
    name : str
        Название подзадачи.
    status : str
        Текущий статус подзадачи.
    priority : str
        Приоритет подзадачи.
    deadline : datetime
        Срок выполнения подзадачи.
    """

    class Meta:
        model = Task
        fields = ["id", "name", "status", "priority", "deadline"]


class TaskReadSerializer(serializers.ModelSerializer):
    """
    Сериализатор для чтения задач.

    Используется для возврата полной информации о задаче вместе с подзадачами.

    Fields
    ------
    id : int
        Идентификатор задачи.
    name : str
        Название задачи.
    executor_name : str
        Полное имя исполнителя задачи.
    author_email : str
        Электронная почта автора задачи.
    subtasks : list of TaskSubtaskSerializer
        Список подзадач.
    status : str
        Статус задачи.
    priority : str
        Приоритет задачи.
    created_at : datetime
        Дата создания задачи.
    updated_at : datetime
        Дата последнего обновления.
    completed_at : datetime or None
        Дата завершения задачи, если задача выполнена.
    time_left : timedelta or None
        Оставшееся время до дедлайна, если задача ещё не завершена.
    is_overdue : bool or None
        Признак просроченной задачи.
    """

    class Meta:
        model = Task
        fields = [
            "id",
            "name",
            "executor_name",
            "author_email",
            "subtasks",
            "status",
            "priority",
            "created_at",
            "updated_at",
            "completed_at",
            "time_left",
            "is_overdue",
        ]

    subtasks = TaskSubtaskSerializer(many=True, read_only=True)
    time_left = SerializerMethodField()
    is_overdue = SerializerMethodField()
    executor_name = serializers.CharField(source="executor.full_name", read_only=True)
    author_email = serializers.CharField(source="author.email", read_only=True)

    @extend_schema_field(OpenApiTypes.DURATION)
    def get_time_left(self, obj):
        """
        Возвращает оставшееся время до дедлайна.

        Parameters
        ----------
        obj : Task
            Объект задачи.

        Returns
        -------
        timedelta or None
            Разница между дедлайном и текущим временем, если задача активна.
        """
        if obj.deadline and obj.status in ["created", "in_progress"]:
            return obj.deadline - timezone.now()
        return None

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_is_overdue(self, obj):
        """
        Определяет, просрочена ли задача.

        Parameters
        ----------
        obj : Task
            Объект задачи.

        Returns
        -------
        bool or None
            True, если срок вышел.
            False, если срок ещё не истёк.
            None, если дедлайн отсутствует или задача завершена.
        """
        time_left = self.get_time_left(obj)
        if time_left is not None:
            return time_left < timedelta(0)
        return None


class TaskWriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания задач.

    Fields
    ------
    name : str
        Название задачи.
    description : str
        Описание задачи.
    priority : str
        Приоритет задачи.
    deadline : datetime, optional
        Дедлайн задачи.
    parent : int, optional
        Идентификатор родительской задачи.
    """

    class Meta:
        model = Task
        fields = [
            "name",
            "description",
            "priority",
            "deadline",
            "parent",
        ]

    def validate(self, attrs):
        """
        Валидирует данные задачи.

        Проверяет дедлайн и корректность связи с родительской задачей.

        Parameters
        ----------
        attrs : dict
            Входные данные.

        Returns
        -------
        dict
            Валидированные данные.
        """
        validators.validate_deadline(attrs, self.instance)
        validators.validate_parent(attrs, self.instance)
        return attrs


class TaskAssignSerializer(serializers.ModelSerializer):
    """
    Сериализатор для назначения исполнителя задачи.

    Fields
    ------
    executor_id : int, optional
        Идентификатор пользователя для назначения исполнителем.
    """

    class Meta:
        model = Task
        fields = ["executor_id"]

    executor_id = serializers.IntegerField(
        required=False, help_text="ID пользователя для назначения"
    )

    def validate_executor_id(self, value):
        """
        Проверяет существование пользователя по указанному ID.

        Parameters
        ----------
        value : int
            ID пользователя.

        Returns
        -------
        int
            Валидированный ID пользователя.

        Raises
        ------
        serializers.ValidationError
            Если пользователь с таким ID не найден.
        """
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("Пользователя с таким ID не существует")
        return value


class ImportantTaskCandidateSerializer(serializers.Serializer):
    """
    Сериализатор кандидатов для выполнения важной задачи.

    Fields
    ------
    task_id : int
        Идентификатор задачи.
    name : str
        Название задачи.
    deadline : datetime
        Дедлайн задачи.
    candidates : list of str
        Список кандидатов на выполнение задачи.
    """
    task_id = serializers.IntegerField(help_text="ID задачи")
    name = serializers.CharField(help_text="Название задачи")
    deadline = serializers.DateTimeField(help_text="Дедлайн задачи")
    candidates = serializers.ListField(
        child=serializers.CharField(), help_text="Список кандидатов на выполнение"
    )
