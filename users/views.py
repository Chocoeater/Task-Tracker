from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.db.models import Count, Q

from users.permissions import IsManagerOrAdmin, IsAdmin
from users.serializers import UserWriteSerializer, UserReadSerializer, MyTokenObtainPairSerializer, UserBusySerializer

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['first_name', 'last_name', 'middle_name', 'email']
    ordering_fields = ['last_name', 'first_name']

    def perform_create(self, serializer):
        user = serializer.save(is_active=True)
        user.set_password(user.password)
        user.save()

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
        elif self.action == 'busy_executors':
            return UserBusySerializer
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

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsManagerOrAdmin])
    def busy_executors(self, request):
        busy_users = (
            User.objects
            .annotate(active_tasks_count=Count('executed_tasks',
                                               filter=Q(executed_tasks__status="in_progress")))
            .filter(active_tasks_count__gt=0)
            .order_by('-active_tasks_count')
        )
        serializer = self.get_serializer(busy_users, many=True)
        return Response(serializer.data)



class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
    permission_classes = [AllowAny]