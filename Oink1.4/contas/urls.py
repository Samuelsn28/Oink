from django.contrib.auth import views as auth
from django.urls import path

from . import views

urlpatterns = [
    path("cadastro/", views.cadastro, name="cadastro"),
    path("perfil/", views.perfil, name="perfil"),
    path("configuracoes/", views.configuracoes, name="configuracoes"),
    path("aceitar-termos/", views.aceitar_termos, name="aceitar_termos"),
    path("apagar/", views.apagar_conta, name="apagar_conta"),
    path("senha/", views.SenhaView.as_view(), name="alterar_senha"),
    path("login/", auth.LoginView.as_view(), name="login"),
    path("logout/", auth.LogoutView.as_view(), name="logout"),
    # recuperar senha pelo e-mail cadastrado
    path("recuperar-senha/", views.RecuperarSenhaView.as_view(), name="password_reset"),
    path("recuperar-senha/enviado/", auth.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("redefinir/<uidb64>/<token>/", auth.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("redefinir/concluido/", auth.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
]
