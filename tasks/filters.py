import django_filters
from tasks.models import Task

class TaskFilter(django_filters.FilterSet):
    deadline_gte = django_filters.DateTimeFilter(field_name='deadline', lookup_expr='gte')
    deadline_lte = django_filters.DateTimeFilter(field_name='deadline', lookup_expr='lte')
    created_at = django_filters.DateTimeFromToRangeFilter()
    executor = django_filters.NumberFilter(field_name='executor', lookup_expr='exact')
    author = django_filters.NumberFilter(field_name='author', lookup_expr='exact')
    parent = django_filters.NumberFilter(field_name='parent', lookup_expr='exact')

    class Meta:
        model = Task
        fields = {
            'status': ['exact'],
            'priority': ['exact'],
        }