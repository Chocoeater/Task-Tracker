import django_filters
from tasks.models import Task


class TaskFilter(django_filters.FilterSet):
    """
    Фильтр для модели Task.

    Позволяет выполнять фильтрацию задач по дате создания, срокам,
    автору, исполнителю и другим полям.

    Attributes
    ----------
    deadline_gte : django_filters.DateTimeFilter
        Фильтр для задач, у которых дедлайн больше или равен указанной дате.
    deadline_lte : django_filters.DateTimeFilter
        Фильтр для задач, у которых дедлайн меньше или равен указанной дате.
    created_at : django_filters.DateTimeFromToRangeFilter
        Фильтр по диапазону дат создания задачи.
    executor : django_filters.NumberFilter
        Фильтр по идентификатору исполнителя задачи.
    author : django_filters.NumberFilter
        Фильтр по идентификатору автора задачи.
    parent : django_filters.NumberFilter
        Фильтр по идентификатору родительской задачи.

    Meta
    ----
    model : Task
        Модель, к которой применяется фильтрация.
    fields : dict
        Поля для фильтрации: статус и приоритет (по точному совпадению).
    """

    deadline_gte = django_filters.DateTimeFilter(
        field_name="deadline", lookup_expr="gte"
    )
    deadline_lte = django_filters.DateTimeFilter(
        field_name="deadline", lookup_expr="lte"
    )
    created_at = django_filters.DateTimeFromToRangeFilter()
    executor = django_filters.NumberFilter(field_name="executor", lookup_expr="exact")
    author = django_filters.NumberFilter(field_name="author", lookup_expr="exact")
    parent = django_filters.NumberFilter(field_name="parent", lookup_expr="exact")

    class Meta:
        model = Task
        fields = {
            "status": ["exact"],
            "priority": ["exact"],
        }
