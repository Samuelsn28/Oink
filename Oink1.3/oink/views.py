import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from financas.resumo import contexto_para_oink

from .ai import ErroIA, perguntar_ao_oink
from .seguranca import contem_cpf

MAX_CARACTERES = 1000
MAX_HISTORICO = 20  # mensagens guardadas na sessão

MSG_CPF = (
    "Oink! 🐷 Parece que você digitou um CPF. Por segurança, eu não aceito dados "
    "pessoais assim, e essa mensagem não foi enviada nem guardada. "
    "Apague o número e mande de novo, tá?"
)
MSG_ERRO = "Oink... 🐷 tive um problema para pensar agora. Tenta de novo em instantes?"


@login_required
def chat(request):
    return render(request, "oink/chat.html")


@require_POST
def enviar(request):
    if not request.user.is_authenticated:
        return JsonResponse({"erro": "Entre na sua conta para falar com o Oink."}, status=401)
    try:
        dados = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"erro": "Pedido inválido."}, status=400)

    mensagem = str(dados.get("mensagem", "")).strip()
    if not mensagem:
        return JsonResponse({"erro": "Escreva uma mensagem."}, status=400)
    if len(mensagem) > MAX_CARACTERES:
        return JsonResponse(
            {"erro": f"Mensagem muito longa (máximo {MAX_CARACTERES} caracteres)."}, status=400
        )

    # Bloqueio ANTES de qualquer coisa: não vai para a sessão, nem para a IA.
    if contem_cpf(mensagem):
        return JsonResponse({"bloqueado": True, "resposta": MSG_CPF})

    historico = request.session.get("historico_oink", [])
    historico.append({"role": "user", "content": mensagem})

    try:
        resposta = perguntar_ao_oink(historico[-MAX_HISTORICO:], contexto_para_oink(request.user))
    except ErroIA:
        # não guarda a pergunta que falhou, para o histórico continuar válido
        return JsonResponse({"erro": MSG_ERRO}, status=502)

    historico.append({"role": "assistant", "content": resposta})
    historico = historico[-MAX_HISTORICO:]
    while historico and historico[0]["role"] != "user":  # a API exige começar por 'user'
        historico.pop(0)
    request.session["historico_oink"] = historico
    return JsonResponse({"resposta": resposta})


@require_POST
def limpar(request):
    if not request.user.is_authenticated:
        return JsonResponse({"ok": False}, status=401)
    request.session.pop("historico_oink", None)
    return JsonResponse({"ok": True})
