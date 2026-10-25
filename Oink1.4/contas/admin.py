from django.contrib import admin

from .models import Perfil


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ("user", "versao_termos", "aceitou_termos_em", "meta_gastos")
    search_fields = ("user__username", "user__email")
