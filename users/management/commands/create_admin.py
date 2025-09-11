from django.contrib.auth import get_user_model
from django.core.management import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    def handle(self, *args, **options):
        user = User.objects.create(email="admin@mail.ru")
        user.first_name = "Одмен"
        user.last_name = "Одменов"
        user.role = "admin"
        user.set_password("1234qwer")
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.save()

        self.stdout.write(self.style.SUCCESS("Админ создан!"))
