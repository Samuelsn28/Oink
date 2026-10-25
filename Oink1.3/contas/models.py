from django.conf import settings
from django.db import models


class Perfil(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perfil")
    foto = models.ImageField("Foto de perfil", upload_to="perfis/", blank=True)
    aceitou_termos_em = models.DateTimeField(null=True, blank=True)
    versao_termos = models.CharField(max_length=20, blank=True)

    @property
    def termos_em_dia(self):
        from django.conf import settings
        return bool(self.aceitou_termos_em) and self.versao_termos == settings.TERMOS_VERSAO
