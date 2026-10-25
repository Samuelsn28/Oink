from django.contrib import messages
from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import CadastroForm, PerfilForm
from .models import Perfil


def cadastro(request):
    if request.user.is_authenticated:
        return redirect("index")
    form = CadastroForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        Perfil.objects.create(user=user, aceitou_termos_em=timezone.now(), versao_termos=settings.TERMOS_VERSAO)
        login(request, user)
        return redirect("index")
    return render(request, "contas/cadastro.html", {"form": form})


@login_required
def perfil(request):
    p, _ = Perfil.objects.get_or_create(user=request.user)
    form = PerfilForm(request.POST or None, request.FILES or None, instance=p, user=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Perfil atualizado!")
        return redirect("perfil")
    return render(request, "contas/perfil.html", {"form": form})


class SenhaView(SuccessMessageMixin, PasswordChangeView):
    template_name = "contas/senha.html"
    success_url = reverse_lazy("perfil")
    success_message = "Senha alterada com sucesso!"


@login_required
def aceitar_termos(request):
    p, _ = Perfil.objects.get_or_create(user=request.user)
    if p.termos_em_dia:
        return redirect("index")
    if request.method == "POST" and request.POST.get("aceito"):
        p.aceitou_termos_em, p.versao_termos = timezone.now(), settings.TERMOS_VERSAO
        p.save(update_fields=["aceitou_termos_em", "versao_termos"])
        return redirect("index")
    return render(request, "contas/aceitar_termos.html")


@login_required
@require_POST
def apagar_conta(request):
    user = request.user
    if not user.check_password(request.POST.get("senha", "")):
        messages.error(request, "Senha incorreta. Sua conta não foi apagada.")
        return redirect("perfil")
    perfil = getattr(user, "perfil", None)
    if perfil and perfil.foto:
        perfil.foto.delete(save=False)          # não deixa a foto sobrando no disco
    logout(request)
    user.delete()                                # apaga também perfil e movimentações
    messages.success(request, "Sua conta foi apagada. O Oink vai sentir saudade!")
    return redirect("login")
