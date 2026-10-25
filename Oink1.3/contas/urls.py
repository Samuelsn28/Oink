from django.urls import path

from . import views

urlpatterns = [
    path("cadastro/", views.cadastro, name="cadastro"),
    path("perfil/", views.perfil, name="perfil"),
    path("aceitar-termos/", views.aceitar_termos, name="aceitar_termos"),
    path("apagar/", views.apagar_conta, name="apagar_conta"),
    path("senha/", views.SenhaView.as_view(), name="alterar_senha"),
]
