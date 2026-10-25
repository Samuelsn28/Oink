from datetime import date

from django.db.models import Sum

from .models import CATEGORIAS


def totais_do_mes(user):
    hoje = date.today()
    mes = user.transacoes.filter(data__year=hoje.year, data__month=hoje.month)
    ganhos = mes.filter(tipo="ganho").aggregate(s=Sum("valor"))["s"] or 0
    gastos = mes.filter(tipo="gasto").aggregate(s=Sum("valor"))["s"] or 0
    return mes, ganhos, gastos


def contexto_para_oink(user):
    """Resumo só com números e categorias fixas (nada de texto livre) para a IA."""
    mes, ganhos, gastos = totais_do_mes(user)
    if not mes.exists():
        return "\n\nO usuário ainda não registrou ganhos nem gastos neste mês no painel."
    nomes = dict(CATEGORIAS)
    por_cat = mes.filter(tipo="gasto").values("categoria").annotate(s=Sum("valor")).order_by("-s")
    linhas = ", ".join(f"{nomes.get(c['categoria'], 'Outros')} R$ {c['s']:.2f}" for c in por_cat) or "nenhum"
    return (
        "\n\nDados reais do usuário neste mês (use para analisar; não invente números):\n"
        f"Ganhos: R$ {ganhos:.2f}\nGastos: R$ {gastos:.2f}\nSaldo: R$ {ganhos - gastos:.2f}\n"
        f"Gastos por categoria: {linhas}"
    )


def gastos_por_categoria(mes, total):
    """Lista para as barras do painel: nome, valor e % do total de gastos."""
    nomes = dict(CATEGORIAS)
    linhas = mes.filter(tipo="gasto").values("categoria").annotate(s=Sum("valor")).order_by("-s")
    return [{"nome": nomes.get(c["categoria"], "Outros"), "valor": c["s"],
             "pct": int(round(c["s"] * 100 / total)) if total else 0} for c in linhas]
