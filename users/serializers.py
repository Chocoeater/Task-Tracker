from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_field
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer, CharField, IntegerField
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils import timezone
from tasks.serializers import TaskReadSerializer

User = get_user_model()


class UserReadSerializer(ModelSerializer):
    full_name = CharField(read_only=True)

    class Meta:
        model = User
        fields = ["id", "full_name", "email", "role", "date_joined", "last_login"]


class UserWriteSerializer(ModelSerializer):
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
        user = User.objects.create(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            middle_name=validated_data.get("middle_name"),  # может быть None
        )
        return user


class UserBusySerializer(ModelSerializer):
    tasks = SerializerMethodField()
    active_tasks_count = IntegerField(read_only=True)

    class Meta:
        model = User
        fields = ["id", "full_name", "email", "active_tasks_count", "tasks"]

    @extend_schema_field(TaskReadSerializer(many=True))
    def get_tasks(self, obj):
        active_tasks = obj.executed_tasks.filter(status="in_progress")
        return TaskReadSerializer(active_tasks, many=True).data


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token["email"] = user.email

        return token

    def validate(self, attrs):  # После верного ввода логина и пароля, но до токена.
        data = super().validate(attrs)
        self.user.last_login = timezone.now()
        self.user.save()  # Обновляется last_login, т.к. в модели auto_now=True
        return data
