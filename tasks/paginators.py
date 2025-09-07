from rest_framework.pagination import PageNumberPagination


class TaskPaginator(PageNumberPagination):
    page_size = 10
