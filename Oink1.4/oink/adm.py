"""Painel do administrador para testar o Oink. Só quem é staff entra; aqui nada é limitado."""
import json
import os
from functools import wraps

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from . import ai
from .seguranca import contem_cpf

MSG_CPF = "Oink! 🐷 (teste) Isso parece um CPF, e seria bloqueado para um usuário comum."


def so_staff(api=False):
    def deco(view):
        @wraps(view)
        def interno(request, *a, **k):
            if not request.user.is_authenticated:
                if api:
                    return JsonResponse({"erro": "Entre na sua conta."}, status=401)
                return redirect_to_login(request.get_full_path())
            if not request.user.is_staff:
                if api:
                    return JsonResponse({"erro": "Só administradores."}, status=403)
                raise PermissionDenied
            return view(request, *a, **k)
        return interno
    return deco


def _json(request):
    try:
        return json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return {}


@so_staff()
def adm_oink(request):
    pasta = settings.BASE_DIR / "static" / "img" / "oink-gifs"
    try:
        gifs = sorted(f[5:-4] for f in os.listdir(pasta) if f.startswith("oink-") and f.endswith(".gif"))
    except OSError:
        gifs = []
    return render(request, "oink/adm.html", {
        "chave_ok": bool(os.getenv("GEMINI_API_KEY", "").strip()),
        "modelo": ai._modelo_ok or "ainda não testado",
        "email_modo": "terminal (teste)" if settings.EMAIL_BACKEND.endswith("console.EmailBackend") else "Gmail",
        "termos_versao": settings.TERMOS_VERSAO,
        "usuarios": User.objects.count(),
        "gifs": gifs,
    })


@so_staff(api=True)
@require_POST
def adm_chat(request):
    d = _json(request)
    hist = d.get("historico")
    if (not isinstance(hist, list) or not hist or len(hist) > 40
            or any(not isinstance(m, dict) or m.get("role") not in ("user", "assistant")
                   or not isinstance(m.get("content"), str) for m in hist)
            or hist[-1]["role"] != "user" or hist[0]["role"] != "user"):
        return JsonResponse({"erro": "Histórico inválido."}, status=400)
    if d.get("bloquear_cpf", True) and contem_cpf(hist[-1]["content"]):
        return JsonResponse({"bloqueado": True, "resposta": MSG_CPF})
    contexto = str(d.get("contexto", ""))[:2000]
    contexto = f"\n\nDados simulados pelo administrador:\n{contexto}" if contexto.strip() else ""
    try:
        resposta = ai.perguntar_ao_oink(hist[-20:], contexto)
    except ai.ErroIA as e:
        return JsonResponse({"erro": f"Falha da IA: {e}"}, status=502)   # o admin vê o erro de verdade
    return JsonResponse({"resposta": resposta})


@so_staff(api=True)
@require_POST
def adm_cpf(request):
    return JsonResponse({"bloqueia": contem_cpf(str(_json(request).get("texto", "")))})


@so_staff(api=True)
@require_POST
def adm_email(request):
    if not request.user.email:
        return JsonResponse({"erro": "Seu usuário não tem e-mail cadastrado (edite em Minha conta)."}, status=400)
    try:
        send_mail("Oink: e-mail de teste", "Se você recebeu isto, o envio de e-mails está funcionando! 🐷",
                  settings.DEFAULT_FROM_EMAIL, [request.user.email])
    except Exception as e:
        return JsonResponse({"erro": f"Falhou: {e}"}, status=502)
    if settings.EMAIL_BACKEND.endswith("console.EmailBackend"):
        return JsonResponse({"mensagem": "Modo teste: o e-mail apareceu no terminal do servidor."})
    return JsonResponse({"mensagem": f"E-mail enviado para {request.user.email}."})
