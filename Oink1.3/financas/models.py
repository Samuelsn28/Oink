from datetime import date
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

CATEGORIAS = [
    ("moradia", "Moradia"), ("alimentacao", "Alimentação"), ("transporte", "Transporte"),
    ("lazer", "Lazer"), ("saude", "Saúde"), ("estudos", "Estudos"),
    ("salario", "Salário"), ("outros", "Outros"),
]


class Transacao(models.Model):
    TIPOS = [("ganho", "Ganho"), ("gasto", "Gasto")]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transacoes")
    tipo = models.CharField(max_length=5, choices=TIPOS)
    descricao = models.CharField("Descrição", max_length=100)
    valor = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    categoria = models.CharField(max_length=20, choices=CATEGORIAS, default="outros")
    data = models.DateField(default=date.today)

    class Meta:
        ordering = ["-data", "-id"]
