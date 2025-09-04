
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from tasks import serializers
from tasks.models import Task
from users.permissions import IsManagerOrAdmin

User = get_user_model()


class TasksViewSet(viewsets.ModelViewSet):

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsManagerOrAdmin]
        else:
            permission_classes = [IsAuthenticated]
        return [perm() for perm in permission_classes]


    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role == 'manager':
            return Task.objects.all()
        return Task.objects.filter(executor=user)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return serializers.TaskReadSerializers
        elif self.action in ['assign']:
            return serializers.TaskAssignSerializer
        return serializers.TaskWriteSerializer

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def assign(self, request, pk=None): # pk, шоб DRF не ругался
        task = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = serializer.validated_data.get('user_id')

        if not user_id:
            target_user = request.user
        else:
            target_user = User.objects.get(id=user_id)

        if request.user.role != 'manager' and not request.user.is_superuser and target_user != request.user:
            return Response({'detail': 'Вы не можете назначать исполнителя'}, status=status.HTTP_403_FORBIDDEN)

        if task.executor is not None:
            return Response(
                {'detail': 'Задача уже взята в работу'},
                status=status.HTTP_400_BAD_REQUEST
            )


        task.executor = target_user
        task.status = 'in_progress'
        task.save(update_fields=['executor', 'status'])

        return Response(
            {'detail': f'Задача "{task.name}" назначена на {target_user.full_name}'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsManagerOrAdmin])
    def release(self, request, pk=None):
        task = self.get_object()

        if task.executor:
            task.executor = None
            task.status = 'created'
            task.save(update_fields=['executor', 'status'])
            return Response(
                {'detail': f'Исполнитель снят с задачи "{task.name}"'},
                status=status.HTTP_200_OK
            )
        return Response(
            {'detail': f'У задачи "{task.name}" отсутствует исполнитель'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def complete(self, request, pk=None):
        task = self.get_object()
        user = request.user

        if task.status == 'in_progress':
            if task.executor == user or user.role == 'manager' or user.is_superuser:
                task.status = 'done'
                task.completed_at = timezone.now()
                task.save(update_fields=['status', 'completed_at'])
                return Response(
                    {'detail': f'Задача "{task.name}" выполнена!'},
                    status=status.HTTP_200_OK
                )
            return Response(
                {'detail': f'Вы не являетесь исполнителем задачи "{task.name}"!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
                {'detail': f'Статус задачи "{task.name}" нельзя изменить'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def free(self, request):
        free_tasks = Task.objects.filter(executor__isnull=True)
        serializer = serializers.TaskReadSerializer(free_tasks, many=True)
        return Response(serializer.data)