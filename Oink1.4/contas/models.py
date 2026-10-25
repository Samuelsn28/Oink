from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Perfil(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perfil")
    foto = models.ImageField("Foto de perfil", upload_to="perfis/", blank=True)
    TONS = [("divertido", "Divertido, com piadinhas"), ("direto", "Direto ao ponto")]
    meta_gastos = models.DecimalField("Meta de gastos do mês (R$)", max_digits=10, decimal_places=2, null=True,
                                      blank=True, validators=[MinValueValidator(0.01)])
    tom_oink = models.CharField("Jeito do Oink falar", max_length=10, choices=TONS, default="divertido")
    usar_dados_no_oink = models.BooleanField("Deixar o Oink ver meus ganhos e gastos", default=True)
    aceitou_termos_em = models.DateTimeField(null=True, blank=True)
    versao_termos = models.CharField(max_length=20, blank=True)

    @property
    def termos_em_dia(self):
        from django.conf import settings
        return bool(self.aceitou_termos_em) and self.versao_termos == settings.TERMOS_VERSAO
