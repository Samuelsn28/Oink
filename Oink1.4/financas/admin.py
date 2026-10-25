from django.contrib import admin

from .models import Transacao


@admin.register(Transacao)
class TransacaoAdmin(admin.ModelAdmin):
    list_display = ("user", "tipo", "descricao", "valor", "categoria", "data")
    list_filter = ("tipo", "categoria")
