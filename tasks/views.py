from rest_framework import viewsets
from tasks import serializers
from tasks.models import Task

class TasksViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role == 'manager':
            return Task.objects.all()
        return Task.objects.filter(executor=user)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return serializers.TaskReadSerializers
        return serializers.TaskWriteSerializer