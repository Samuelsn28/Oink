from django.urls import path

from . import adm, views

urlpatterns = [
    path("oink/", views.chat, name="chat"),
    path("api/oink/", views.enviar, name="oink_enviar"),
    path("api/oink/limpar/", views.limpar, name="oink_limpar"),
    path("painel-adm/", adm.adm_oink, name="adm_oink"),
    path("api/adm/chat/", adm.adm_chat, name="adm_chat"),
    path("api/adm/cpf/", adm.adm_cpf, name="adm_cpf"),
    path("api/adm/email/", adm.adm_email, name="adm_email"),
]
