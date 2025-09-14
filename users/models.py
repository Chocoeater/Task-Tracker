from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Кастомная модель пользователя.

    Используется e-mail в качестве уникального идентификатора (USERNAME_FIELD).
    Добавлены дополнительные поля: отчество (middle_name) и роль пользователя (role).

    Атрибуты
    --------
    email : models.EmailField
        Уникальный e-mail пользователя. Используется для входа в систему.
    first_name : models.CharField
        Имя пользователя. Может быть пустым.
    last_name : models.CharField
        Фамилия пользователя. Может быть пустой.
    middle_name : models.CharField
        Отчество пользователя. Может быть пустым или отсутствовать.
    role : models.CharField
        Роль пользователя: ``manager`` (Менеджер) или ``developer`` (Разработчик).
        По умолчанию — ``developer``.
    created_at : models.DateTimeField
        Дата и время создания пользователя (устанавливается автоматически).
    updated_at : models.DateTimeField
        Дата и время последнего обновления пользователя (устанавливается автоматически).

    Свойства
    --------
    full_name : str
        Полное имя пользователя в формате: "Фамилия Имя Отчество".
        Если отчество отсутствует — возвращает "Фамилия Имя".
        Если ФИО пустое — возвращает e-mail.

    Метаданные
    ----------
    verbose_name : str
        Человекочитаемое название модели — "пользователь".
    verbose_name_plural : str
        Человекочитаемое название модели во множественном числе — "пользователи".

    Примечания
    ----------
    - Поле ``username`` отключено, вместо него используется ``email``.
    - Поля, обязательные при создании: ``first_name``, ``last_name``.
    """
    email = models.EmailField(
        unique=True, verbose_name="E-mail", help_text="Введите адрес электронной почты"
    )
    username = None
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    middle_name = models.CharField(max_length=150, blank=True, null=True)

    role = models.CharField(
        max_length=50,
        choices=[
            ("manager", "Менеджер"),
            ("developer", "Разработчик"),
        ],
        default="developer",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = "пользователь"
        verbose_name_plural = "пользователи"

    def __str__(self):
        return f"{self.full_name}"

    @property
    def full_name(self):
        """ФИО: Фамилия Имя Отчество (или без отчества)."""
        parts = [self.last_name, self.first_name, self.middle_name]
        full = " ".join(p for p in parts if p)
        return full.strip() if full else self.email
