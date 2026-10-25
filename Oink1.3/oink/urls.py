from django.urls import path

from . import views

urlpatterns = [
    path("oink/", views.chat, name="chat"),
    path("api/oink/", views.enviar, name="oink_enviar"),
    path("api/oink/limpar/", views.limpar, name="oink_limpar"),
]
