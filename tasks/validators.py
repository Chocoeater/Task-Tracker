from django.utils import timezone

from rest_framework.exceptions import ValidationError


def validate_deadline(attrs, instance=None):
    deadline = attrs.get("deadline", None)

    if instance:
        if deadline is None:
            deadline = instance.deadline

    if deadline < timezone.now():
        raise ValidationError("Дедлайн не может быть меньше даты создания")


def validate_parent(attrs, instance=None):
    parent = attrs.get("parent", None)
    id = attrs.get("id", None)

    if instance:
        if parent is None:
            parent = instance.parent

    if parent:
        if parent.id == id:
            raise ValidationError("Задача не может быть родителем для самой себя")
