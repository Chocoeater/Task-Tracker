from django.urls import path
from rest_framework.routers import DefaultRouter
from users import views

from .views import MyTokenObtainPairView
from users.apps import UsersConfig


app_name = UsersConfig.name

router = DefaultRouter()
router.register(r"", views.UserViewSet, basename="users")

urlpatterns = [
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
]  + router.urls

