from datetime import timedelta

from django.utils import timezone
from rest_framework.fields import SerializerMethodField, CharField
from rest_framework.serializers import ModelSerializer

from tasks import validators
from tasks.models import Task

class TaskSubtaskSerializer(ModelSerializer):
    """Подзадачи"""
    class Meta:
        model = Task
        fields = ["id", "name", "status", "priority", "deadline"]


class TaskReadSerializers(ModelSerializer):
    """Для чтения таски"""
    subtasks = TaskSubtaskSerializer(many=True, read_only=True)
    time_left = SerializerMethodField()
    is_overdue = SerializerMethodField()
    executor_name = CharField(source="executor.full_name", read_only=True)
    author_email = CharField(source="author.email", read_only=True)

    def get_time_left(self, obj):
        if obj.deadline and obj.status in ['created', 'in_progress']:
            return obj.deadline - timezone.now()
        return None

    def get_is_overdue(self, obj):
        time_left = self.get_time_left(obj)
        if time_left is not None:
            return time_left < timedelta(0)
        return None

    class Meta:
        model = Task
        fields = [
            'executor_name',
            'author_email',
            'subtasks',
            'status',
            'priority',
            'created_at',
            'updated_at',
            'completed_at',
            'time_left',
            'is_overdue'
        ]

class TaskWriteSerializer(ModelSerializer):
    """Для создания таски"""
    class Meta:
        model = Task
        fields = [
            'name',
            'description',
            'priority',
            'deadline',
            'parent',
        ]
    def validate(self, attrs):
        validators.validate_deadline(attrs, self.instance)
        validators.validate_parent(attrs, self.instance)
        return attrs