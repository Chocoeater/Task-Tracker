from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from tasks import serializers
from tasks.models import Task
from users.permissions import IsManagerOrAdmin, IsExecutor
from django.db.models import Q


class TasksViewSet(viewsets.ModelViewSet):

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'delete']:
            permission_classes = [IsAuthenticated, IsManagerOrAdmin]
        elif self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsExecutor] # take
        return [perm() for perm in permission_classes]


    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role == 'manager':
            return Task.objects.all()
        return Task.objects.filter(Q(executor=user) | Q(executor__isnull=True))

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return serializers.TaskReadSerializers
        return serializers.TaskWriteSerializer

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def take(self, request, pk=None): # pk, шоб DRF не ругался
        task = self.get_object()

        if task.executor is not None:
            return Response(
                {'detail': 'Задача уже взята в работу'},
                status=status.HTTP_400_BAD_REQUEST
            )

        task.executor = request.user
        task.status = 'in_progress'
        task.save(update_fields=['executor', 'status'])

        return Response(
            {'detail': f'Задача назначена на {request.user.full_name}'},
            status=status.HTTP_200_OK
        )