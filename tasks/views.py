from django.contrib.auth import get_user_model
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from tasks import serializers
from tasks.filters import TaskFilter
from tasks.models import Task
from tasks.paginators import TaskPaginator
from tasks.services import get_important_task_and_candidates, all_subtasks_is_done
from users.permissions import IsManagerOrAdmin

User = get_user_model()


@extend_schema_view(
    list=extend_schema(
        summary="Список задач",
        description="Возвращает список задач. "
        "Для обычного пользователя — только его задачи, для менеджера/админа — все.",
    ),
    retrieve=extend_schema(
        summary="Детали задачи", description="Возвращает полную информацию о задаче."
    ),
    create=extend_schema(
        summary="Создание задачи",
        description="Доступно только менеджеру или администратору.",
    ),
    update=extend_schema(summary="Обновление задачи"),
    partial_update=extend_schema(summary="Частичное обновление задачи"),
    destroy=extend_schema(summary="Удаление задачи"),
)
class TasksViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с задачами.

    Предоставляет CRUD-операции и дополнительные действия:
    назначение исполнителя, снятие исполнителя, завершение задачи,
    а также выборка свободных и важных задач.

    Attributes
    ----------
    pagination_class : TaskPaginator
        Пагинация для списка задач.
    filter_backends : list
        Список фильтров (DjangoFilterBackend, SearchFilter, OrderingFilter).
    filterset_class : TaskFilter
        Класс фильтрации для задач.
    search_fields : list of str
        Поля для поиска (`name`, `description`).
    ordering_fields : list of str
        Поля для сортировки (`deadline`, `priority`, `created_at`).
    ordering : list
        Поле сортировки по умолчанию (`-created_at`).

    Methods
    -------
    get_permissions()
        Определяет права доступа для действия.
    get_queryset()
        Возвращает queryset в зависимости от роли пользователя.
    get_serializer_class()
        Определяет сериализатор для конкретного действия.
    assign(request, pk=None)
        Назначает исполнителя задачи.
    release(request, pk=None)
        Снимает исполнителя с задачи.
    complete(request, pk=None)
        Отмечает задачу как выполненную.
    free(request)
        Возвращает список задач без исполнителя.
    important(request)
        Возвращает список приоритетных задач и кандидатов на выполнение.
    """
    pagination_class = TaskPaginator
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    filterset_class = TaskFilter

    search_fields = ["name", "description"]
    ordering_fields = ["deadline", "priority", "created_at"]
    ordering = ["-created_at"]

    def get_permissions(self):
        """
        Определяет права доступа в зависимости от действия.

        Returns
        -------
        list
            Список экземпляров классов разрешений.
        """
        if self.action in [
            "create",
            "update",
            "partial_update",
            "destroy",
            "release",
            "important",
        ]:
            permission_classes = [IsAuthenticated, IsManagerOrAdmin]
        else:
            permission_classes = [IsAuthenticated]
        return [perm() for perm in permission_classes]

    def get_queryset(self):
        """
        Возвращает queryset задач в зависимости от роли пользователя.

        Returns
        -------
        QuerySet
            Отфильтрованный список задач.
        """

        user = self.request.user

        if getattr(self, "swagger_fake_view", False) or not user.is_authenticated:
            return Task.objects.none()  # Чтобы spec не ругался

        qs = Task.objects.all()
        if not (
            user.is_superuser
            or user.role == "manager"
            or self.action in ["assign", "release"]
        ):
            qs = qs.filter(executor=user)
        return qs

    def get_serializer_class(self):
        """
        Определяет сериализатор для текущего действия.

        Returns
        -------
        Serializer
            Класс сериализатора.
        """
        if self.action in ["list", "retrieve"]:
            return serializers.TaskReadSerializer
        elif self.action in ["assign"]:
            return serializers.TaskAssignSerializer
        return serializers.TaskWriteSerializer

    @extend_schema(
        summary="Назначить исполнителя",
        description="Назначает исполнителя на задачу. "
        "Менеджер/админ может назначить любого пользователя, обычный пользователь — только себя.",
        responses={
            200: OpenApiResponse(description="Задача назначена"),
            400: OpenApiResponse(description="Задача уже взята или ошибка валидации"),
            403: OpenApiResponse(description="Нет прав назначить исполнителя"),
        },
    )
    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        """
        Назначает исполнителя на задачу.

        Parameters
        ----------
        request : Request
            Объект HTTP-запроса.
        pk : int, optional
            ID задачи.

        Returns
        -------
        Response
            Подтверждение назначения или ошибка.
        """
        task = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = serializer.validated_data.get("executor_id")

        if not user_id:
            target_user = request.user
        else:
            target_user = User.objects.get(id=user_id)

        if (
            request.user.role != "manager"
            and not request.user.is_superuser
            and target_user != request.user
        ):
            return Response(
                {"detail": "Вы не можете назначать исполнителя"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if task.executor is not None:
            return Response(
                {"detail": "Задача уже взята в работу"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        task.executor = target_user
        task.status = "in_progress"
        task.save(update_fields=["executor", "status"])

        return Response(
            {"detail": f'Задача "{task.name}" назначена на {target_user.full_name}'},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Снять исполнителя",
        description="Снимает исполнителя с задачи. Доступно только менеджеру или администратору.",
        request=None,
        responses={
            200: OpenApiResponse(description="Исполнитель снят"),
            400: OpenApiResponse(description="У задачи нет исполнителя"),
        },
    )
    @action(detail=True, methods=["post"])
    def release(self, request, pk=None):
        """
        Снимает исполнителя с задачи.

        Parameters
        ----------
        request : Request
            Объект HTTP-запроса.
        pk : int, optional
            ID задачи.

        Returns
        -------
        Response
            Подтверждение снятия или ошибка.
        """
        task = self.get_object()

        if task.executor:
            task.executor = None
            task.status = "created"
            task.save(update_fields=["executor", "status"])
            return Response(
                {"detail": f'Исполнитель снят с задачи "{task.name}"'},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"detail": f'У задачи "{task.name}" отсутствует исполнитель'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(
        summary="Завершить задачу",
        description="Отмечает задачу как выполненную. Может сделать сам исполнитель, менеджер или админ.",
        request=None,
        responses={
            200: OpenApiResponse(description="Задача завершена"),
            400: OpenApiResponse(description="Нельзя завершить задачу"),
        },
    )
    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """
        Отмечает задачу как выполненную.

        Parameters
        ----------
        request : Request
            Объект HTTP-запроса.
        pk : int, optional
            ID задачи.

        Returns
        -------
        Response
            Подтверждение выполнения или ошибка.
        """
        task = self.get_object()
        user = request.user

        if task.status == "in_progress":
            if task.executor == user or user.role == "manager" or user.is_superuser:
                task.status = "done"
                task.completed_at = timezone.now()
                task.save(update_fields=["status", "completed_at"])
                if task.parent:
                    if all_subtasks_is_done(task.parent):
                        task.parent.status = "done"
                        task.parent.completed_at = timezone.now()
                        task.save(update_fields=["status", "completed_at"])
                return Response(
                    {"detail": f'Задача "{task.name}" выполнена!'},
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"detail": f'Вы не являетесь исполнителем задачи "{task.name}"!'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {"detail": f'Статус задачи "{task.name}" нельзя изменить'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(
        summary="Свободные задачи",
        description="Возвращает список задач без исполнителя.",
        responses={200: serializers.TaskReadSerializer(many=True)},
    )
    @action(detail=False, methods=["get"], pagination_class=None)
    def free(self, request):
        """
        Возвращает список задач без исполнителя.

        Parameters
        ----------
        request : Request
            Объект HTTP-запроса.

        Returns
        -------
        Response
            Список свободных задач.
        """
        free_tasks = Task.objects.filter(executor__isnull=True)
        serializer = serializers.TaskReadSerializer(free_tasks, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Важные задачи",
        description="Возвращает список приоритетных задач и кандидатов на исполнение.",
        responses={200: serializers.ImportantTaskCandidateSerializer(many=True)},
    )
    @action(detail=False, methods=["get"], pagination_class=None)
    def important(self, request):
        """
       Возвращает список приоритетных задач и кандидатов на выполнение.

       Parameters
       ----------
       request : Request
           Объект HTTP-запроса.

       Returns
       -------
       Response
           Список задач и кандидатов.
       """
        data = get_important_task_and_candidates()
        serializer = serializers.ImportantTaskCandidateSerializer(data, many=True)
        return Response(serializer.data)
