from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_field
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer, CharField, IntegerField
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils import timezone
from tasks.serializers import TaskReadSerializer

User = get_user_model()


class UserReadSerializer(ModelSerializer):
    """
    Сериализатор для чтения информации о пользователях.

    Fields
    ------
    id : int
        Идентификатор пользователя.
    full_name : str
        Полное имя пользователя (Фамилия Имя Отчество).
    email : str
        Электронная почта пользователя.
    role : str
        Роль пользователя (manager/developer).
    date_joined : datetime
        Дата регистрации пользователя.
    last_login : datetime
        Дата последнего входа пользователя.
    """
    full_name = CharField(read_only=True)

    class Meta:
        model = User
        fields = ["id", "full_name", "email", "role", "date_joined", "last_login"]


class UserWriteSerializer(ModelSerializer):
    """
    Сериализатор для создания и обновления пользователя.

    Fields
    ------
    id : int
        Идентификатор пользователя.
    email : str
        Электронная почта пользователя.
    password : str
        Пароль пользователя (write-only).
    first_name : str
        Имя пользователя.
    last_name : str
        Фамилия пользователя.
    middle_name : str, optional
        Отчество пользователя.
    """
    password = CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "password",
            "first_name",
            "last_name",
            "middle_name",
        ]

    def create(self, validated_data):
        """
        Создает нового пользователя.

        Parameters
        ----------
        validated_data : dict
            Валидированные данные из запроса.

        Returns
        -------
        User
            Созданный экземпляр пользователя.
        """
        user = User.objects.create(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            middle_name=validated_data.get("middle_name"),  # может быть None
        )
        return user


class UserBusySerializer(ModelSerializer):
    """
    Сериализатор для пользователя с активными задачами.

    Fields
    ------
    id : int
        Идентификатор пользователя.
    full_name : str
        Полное имя пользователя.
    email : str
        Электронная почта пользователя.
    active_tasks_count : int
        Количество активных задач (в работе).
    tasks : list of TaskReadSerializer
        Список активных задач пользователя.
    """
    tasks = SerializerMethodField()
    active_tasks_count = IntegerField(read_only=True)

    class Meta:
        model = User
        fields = ["id", "full_name", "email", "active_tasks_count", "tasks"]

    @extend_schema_field(TaskReadSerializer(many=True))
    def get_tasks(self, obj):
        """
        Возвращает список активных задач пользователя.

        Parameters
        ----------
        obj : User
            Экземпляр пользователя.

        Returns
        -------
        list
            Сериализованные данные задач (TaskReadSerializer).
        """
        active_tasks = obj.executed_tasks.filter(status="in_progress")
        return TaskReadSerializer(active_tasks, many=True).data


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Кастомный сериализатор для получения JWT токена.

    Добавляет email пользователя в payload токена
    и обновляет last_login после успешного входа.
    """
    @classmethod
    def get_token(cls, user):
        """
        Генерирует токен с добавленным полем email.

        Parameters
        ----------
        user : User
            Пользователь, для которого создается токен.

        Returns
        -------
        RefreshToken
            JWT токен пользователя.
        """
        token = super().get_token(user)

        token["email"] = user.email

        return token

    def validate(self, attrs):
        """
        Валидирует логин и пароль, обновляет last_login.

        Parameters
        ----------
        attrs : dict
            Входные данные (email и password).

        Returns
        -------
        dict
            Данные токена (access и refresh).
        """
        data = super().validate(attrs)
        self.user.last_login = timezone.now()
        self.user.save()
        return data
