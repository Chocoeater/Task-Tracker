from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.db.models import Count, Q

from users.permissions import IsManagerOrAdmin, IsAdmin
from users.serializers import (
    UserWriteSerializer,
    UserReadSerializer,
    MyTokenObtainPairSerializer,
    UserBusySerializer,
)

User = get_user_model()


@extend_schema_view(
    list=extend_schema(
        summary="Список пользователей",
        description="Возвращает список всех пользователей. Доступно менеджеру или администратору.",
    ),
    retrieve=extend_schema(
        summary="Детали пользователя",
        description="Возвращает полную информацию о пользователе.",
    ),
    create=extend_schema(
        summary="Создание пользователя", description="Доступно только администратору."
    ),
    update=extend_schema(summary="Обновление пользователя"),
    partial_update=extend_schema(summary="Частичное обновление пользователя"),
    destroy=extend_schema(summary="Удаление пользователя"),
)
class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с пользователями.

    Предоставляет CRUD-операции и дополнительные действия:
    просмотр своей учетной записи и выборка занятых исполнителей.

    Attributes
    ----------
    queryset : QuerySet
        Все пользователи.
    filter_backends : list
        Список фильтров (DjangoFilterBackend, SearchFilter, OrderingFilter).
    search_fields : list of str
        Поля для поиска (first_name, last_name, middle_name, email).
    ordering_fields : list of str
        Поля для сортировки (last_name, first_name).

    Methods
    -------
    perform_create(serializer)
        Создает нового пользователя с хешированным паролем.
    get_permissions()
        Определяет права доступа для действия.
    get_serializer_class()
        Определяет сериализатор для конкретного действия.
    me(request)
        Возвращает или обновляет данные текущего пользователя.
    busy_executors(request)
        Возвращает список пользователей с активными задачами.
    """
    queryset = User.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["first_name", "last_name", "middle_name", "email"]
    ordering_fields = ["last_name", "first_name"]

    def perform_create(self, serializer):
        """
        Создает нового пользователя.

        Parameters
        ----------
        serializer : UserWriteSerializer
            Сериализатор с данными пользователя.

        Notes
        -----
        - Устанавливает пароль пользователя через set_password.
        - Активирует пользователя (is_active=True).
        """
        user = serializer.save(is_active=True)
        user.set_password(user.password)
        user.save()

    def get_permissions(self):
        """
        Определяет права доступа в зависимости от действия.

        Returns
        -------
        list
            Список экземпляров классов разрешений.
        """
        if self.action == "list":
            permission_classes = [IsAuthenticated, IsManagerOrAdmin]
        elif self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [IsAuthenticated, IsAdmin]
        elif self.action == "me":
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsManagerOrAdmin]
        return [perm() for perm in permission_classes]

    def get_serializer_class(self):
        """
        Определяет сериализатор для текущего действия.

        Returns
        -------
        Serializer
            Класс сериализатора.
        """
        if self.action in ["create", "update", "partial_update"]:
            return UserWriteSerializer
        elif self.action == "busy_executors":
            return UserBusySerializer
        return UserReadSerializer

    @extend_schema(
        summary="Моя учётная запись",
        description="Возвращает или обновляет информацию о текущем пользователе.",
        responses={
            200: UserReadSerializer,
            400: OpenApiResponse(description="Ошибка валидации"),
        },
    )
    @action(
        detail=False, methods=["get", "patch"], permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        """
        Возвращает или обновляет данные текущего пользователя.

        Parameters
        ----------
        request : Request
            Объект HTTP-запроса.

        Returns
        -------
        Response
            Сериализованные данные пользователя или ошибки валидации.
        """

        user = request.user

        if request.method == "GET":
            serializer = UserReadSerializer(user)
            return Response(serializer.data)

        if request.method == "PATCH":
            serializer = UserWriteSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    @extend_schema(
        summary="Занятые исполнители",
        description="Возвращает список пользователей, у которых есть активные задачи.",
        responses={200: UserBusySerializer(many=True)},
    )
    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated, IsManagerOrAdmin],
    )
    def busy_executors(self, request):
        """
        Возвращает список пользователей с активными задачами.

        Parameters
        ----------
        request : Request
            Объект HTTP-запроса.

        Returns
        -------
        Response
            Список пользователей с количеством активных задач и деталями задач.
        """
        busy_users = (
            User.objects.annotate(
                active_tasks_count=Count(
                    "executed_tasks", filter=Q(executed_tasks__status="in_progress")
                )
            )
            .filter(active_tasks_count__gt=0)
            .order_by("-active_tasks_count")
        )
        serializer = self.get_serializer(busy_users, many=True)
        return Response(serializer.data)


@extend_schema(
    summary="Получение токена", description="Возвращает токены для авторизации"
)
class MyTokenObtainPairView(TokenObtainPairView):
    """
    Вью для получения JWT токенов пользователя.

    Использует кастомный сериализатор MyTokenObtainPairSerializer,
    который добавляет email в payload токена и обновляет last_login.

    Attributes
    ----------
    serializer_class : MyTokenObtainPairSerializer
        Сериализатор для токена.
    permission_classes : list
        Список разрешений (AllowAny).
    """
    serializer_class = MyTokenObtainPairSerializer
    permission_classes = [AllowAny]
