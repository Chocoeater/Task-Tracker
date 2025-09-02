from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True, verbose_name="E-mail", help_text="Введите адрес электронной почты")
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
    REQUIRED_FIELDS = ['first_name', 'last_name']

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

