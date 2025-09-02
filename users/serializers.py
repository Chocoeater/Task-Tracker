from django.contrib.auth import get_user_model
from rest_framework.serializers import ModelSerializer, CharField

User = get_user_model()

class UserReadSerializer(ModelSerializer):
    full_name = CharField(source="full_name", read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'full_name',
            'email',
            'role',
            'date_joined',
            'last_login'
        ]

class UserWriteSerializer(ModelSerializer):
    password = CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'password',
            'first_name',
            'last_name',
            'middle_name',
        ]

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            middle_name=validated_data.get('middle_name') # может быть None
        )
        return user
