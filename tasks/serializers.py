from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.fields import SerializerMethodField
from rest_framework import serializers

from tasks import validators
from tasks.models import Task

User = get_user_model()

class TaskSubtaskSerializer(serializers.ModelSerializer):
    """Подзадачи"""
    class Meta:
        model = Task
        fields = ["id", "name", "status", "priority", "deadline"]


class TaskReadSerializer(serializers.ModelSerializer):
    """Для чтения таски"""

    class Meta:
        model = Task
        fields = [
            'id',
            'name',
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

    subtasks = TaskSubtaskSerializer(many=True, read_only=True)
    time_left = SerializerMethodField()
    is_overdue = SerializerMethodField()
    executor_name = serializers.CharField(source="executor.full_name", read_only=True)
    author_email = serializers.CharField(source="author.email", read_only=True)

    def get_time_left(self, obj):
        if obj.deadline and obj.status in ['created', 'in_progress']:
            return obj.deadline - timezone.now()
        return None

    def get_is_overdue(self, obj):
        time_left = self.get_time_left(obj)
        if time_left is not None:
            return time_left < timedelta(0)
        return None



class TaskWriteSerializer(serializers.ModelSerializer):
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

class TaskAssignSerializer(serializers.ModelSerializer):

    class Meta:
        model = Task
        fields = ['executor_id']

    executor_id = serializers.IntegerField(required=False, help_text='ID пользователя для назначения')

    def validate_executor_id(self, value):
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError('Пользователя с таким ID не существует')
        return value

