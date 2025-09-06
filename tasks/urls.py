from django.urls import path
from rest_framework.routers import DefaultRouter
from tasks import views

from tasks.apps import TasksConfig


app_name = TasksConfig.name

router = DefaultRouter()
router.register(r"", views.TasksViewSet, basename="tasks")

urlpatterns = [

]  + router.urls

