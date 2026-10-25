from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("transacao/<int:pk>/excluir/", views.excluir, name="excluir"),
    path("sobre/", views.sobre, name="sobre"),
    path("por-que-usar/", views.pq_usar, name="pq_usar"),
    path("termos/", views.termos, name="termos"),
]
