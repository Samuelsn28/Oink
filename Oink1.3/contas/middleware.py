from django.http import JsonResponse
from django.shortcuts import redirect

# Quem ainda não aceitou os Termos de uso só alcança estas rotas.
LIVRES = ("/termos/", "/contas/aceitar-termos/", "/contas/logout/", "/contas/apagar/", "/media/", "/static/")


class TermosMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        u = request.user
        if u.is_authenticated and not request.path.startswith(LIVRES):
            perfil = getattr(u, "perfil", None)
            if not (perfil and perfil.termos_em_dia):
                if request.path.startswith("/api/"):
                    return JsonResponse({"erro": "Aceite os Termos de uso para continuar."}, status=403)
                return redirect("aceitar_termos")
        return self.get_response(request)
