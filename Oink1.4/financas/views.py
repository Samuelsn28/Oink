from datetime import date

from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import TransacaoForm
from .models import Transacao
from .resumo import gastos_por_categoria, totais_do_mes

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]


@login_required
def index(request):
    form = TransacaoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        t = form.save(commit=False)
        t.user = request.user
        t.save()
        return redirect(f"{reverse('index')}?novo={t.tipo}")
    mes, ganhos, gastos = totais_do_mes(request.user)
    perfil = getattr(request.user, "perfil", None)
    foto = perfil.foto if perfil and perfil.foto else None
    meta = perfil.meta_gastos if perfil else None
    meta_pct = int(gastos * 100 / meta) if meta else 0
    novo = request.GET.get("novo")
    if novo == "ganho":
        humor, frase = "comemorando", "Mais um ganho no cofrinho!"
    elif novo == "gasto":
        humor, frase = "pensando", "Hmm… vamos ver se esse gasto cabe no mês."
    elif not mes.exists():
        humor, frase = "dormindo", "Zzz… registre seu primeiro ganho ou gasto para me acordar."
    elif meta and gastos > meta:
        humor, frase = "preocupado", "Passou da meta de gastos do mês. Bora revisar?"
    elif ganhos < gastos:
        humor, frase = "preocupado", "Opa, o mês está no vermelho. Vamos olhar os gastos?"
    elif gastos * 2 <= ganhos:
        humor, frase = "comemorando", "Uhul! Você gastou menos da metade do que ganhou."
    else:
        humor, frase = "feliz", "Tudo certo por aqui. Continue assim!"
    return render(request, "index.html", {
        "humor": humor, "frase_oink": frase, "meta": meta, "meta_pct": meta_pct,
        "nome": request.user.first_name or request.user.username,
        "foto_url": foto.url if foto else "",
        "ganhos": ganhos, "gastos": gastos, "saldo": ganhos - gastos,
        "categorias": gastos_por_categoria(mes, gastos),
        "mes_nome": MESES[date.today().month - 1],
        "ultimas": request.user.transacoes.all()[:10],
        "form": form,
    })


@login_required
@require_POST
def excluir(request, pk):
    get_object_or_404(Transacao, pk=pk, user=request.user).delete()
    return redirect("index")


def sobre(request):
    return render(request, "sobre.html")


def pq_usar(request):
    return render(request, "pq_usar.html")


def termos(request):
    return render(request, "termos.html")
