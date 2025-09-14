from django.utils import timezone

from rest_framework.exceptions import ValidationError


def validate_deadline(attrs, instance=None):
    """
    Проверяет корректность дедлайна задачи.

    Если дедлайн указан и он меньше текущего времени,
    возбуждается исключение ValidationError.

    Parameters
    ----------
    attrs : dict
        Входные данные для сериализатора или модели.
    instance : Task, optional
        Экземпляр задачи (используется при обновлении).

    Raises
    ------
    ValidationError
        Если дедлайн меньше текущей даты и времени.
    """
    deadline = attrs.get("deadline", None)

    if instance:
        if deadline is None:
            deadline = instance.deadline

    if deadline < timezone.now():
        raise ValidationError("Дедлайн не может быть меньше даты создания")


def validate_parent(attrs, instance=None):
    """
    Проверяет корректность связи с родительской задачей.

    Задача не может быть назначена родителем самой себе.

    Parameters
    ----------
    attrs : dict
        Входные данные для сериализатора или модели.
    instance : Task, optional
        Экземпляр задачи (используется при обновлении).

    Raises
    ------
    ValidationError
        Если задача указана как родитель самой себе.
    """
    parent = attrs.get("parent", None)
    id = attrs.get("id", None)

    if instance:
        if parent is None:
            parent = instance.parent

    if parent:
        if parent.id == id:
            raise ValidationError("Задача не может быть родителем для самой себя")
