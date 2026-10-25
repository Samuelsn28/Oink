from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Perfil


def novo_usuario(username, email="", password="x", aceito=True):
    u = User.objects.create_user(username, email, password)
    Perfil.objects.create(user=u, aceitou_termos_em=timezone.now() if aceito else None,
                          versao_termos=settings.TERMOS_VERSAO if aceito else "")
    return u
