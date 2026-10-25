from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Dá acesso de administrador (painel de testes do Oink e /admin/) a um usuário."

    def add_arguments(self, parser):
        parser.add_argument("usuario")

    def handle(self, *args, **opts):
        try:
            u = User.objects.get(username=opts["usuario"])
        except User.DoesNotExist:
            raise CommandError("Usuário não encontrado.")
        u.is_staff = u.is_superuser = True
        u.save(update_fields=["is_staff", "is_superuser"])
        self.stdout.write(f"{u.username} agora é administrador.")
