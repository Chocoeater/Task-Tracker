from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from users.permissions import IsManagerOrAdmin, IsAdmin
from users.serializers import UserWriteSerializer, UserReadSerializer

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()

    def get_permissions(self):
        if self.action == 'list':
            permission_classes = [IsAuthenticated, IsManagerOrAdmin]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsAdmin]
        else:
            permission_classes = [IsAuthenticated, IsManagerOrAdmin]
        return [perm() for perm in permission_classes]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return UserWriteSerializer
        return UserReadSerializer

    @action(detail=False, methods=['get', 'patch'], permission_classes=[IsAuthenticated])
    def me(self, request):

        user = request.user

        if request.method == 'GET':
            serializer = UserReadSerializer(user)
            return Response(serializer.data)

        if request.method == 'PATCH':
            serializer = UserWriteSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer