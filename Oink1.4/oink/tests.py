from unittest.mock import patch

from django.contrib.auth.models import User

from contas.testutils import novo_usuario
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .ai import ErroIA
from .seguranca import contem_cpf, cpf_valido


class CpfTests(SimpleTestCase):
    def test_bloqueia(self):
        for t in [
            "meu cpf é 529.982.247-25",
            "52998224725",
            "529 982 247 25",
            "529-982-247-25",
            "cpf: 529.982.247.25",
            "123.456.789-00",  # formato clássico, mesmo inválido
        ]:
            self.assertTrue(contem_cpf(t), t)

    def test_nao_bloqueia(self):
        for t in [
            "meu telefone é 11987654321",
            "gastei 12345678901 centavos",
            "ganho R$ 3.500,00 por mês",
            "11111111111",
            "CEP 08460-000",
            "",
        ]:
            self.assertFalse(contem_cpf(t), t)

    def test_digitos_verificadores(self):
        self.assertTrue(cpf_valido("52998224725"))
        self.assertFalse(cpf_valido("52998224726"))
        self.assertFalse(cpf_valido("11111111111"))


class ChatTests(TestCase):
    def setUp(self):
        self.client.force_login(novo_usuario("ana", password="x"))

    def post(self, texto):
        return self.client.post(
            reverse("oink_enviar"), {"mensagem": texto}, content_type="application/json"
        )

    @patch("oink.views.perguntar_ao_oink")
    def test_cpf_nao_chega_na_ia_nem_na_sessao(self, ia):
        r = self.post("meu cpf é 529.982.247-25")
        self.assertTrue(r.json()["bloqueado"])
        ia.assert_not_called()
        self.assertNotIn("historico_oink", self.client.session)

    @patch("oink.views.perguntar_ao_oink", return_value="Oink! Oi!")
    def test_fluxo_normal_guarda_historico(self, ia):
        r = self.post("Como economizar?")
        self.assertEqual(r.json()["resposta"], "Oink! Oi!")
        self.assertEqual(len(self.client.session["historico_oink"]), 2)

    @patch("oink.views.perguntar_ao_oink", side_effect=ErroIA("x"))
    def test_erro_da_ia_nao_suja_historico(self, ia):
        r = self.post("Oi")
        self.assertEqual(r.status_code, 502)
        self.assertNotIn("historico_oink", self.client.session)

    def test_mensagem_vazia_e_longa(self):
        self.assertEqual(self.post("   ").status_code, 400)
        self.assertEqual(self.post("a" * 1001).status_code, 400)

    def test_json_invalido(self):
        r = self.client.post(reverse("oink_enviar"), "{x", content_type="application/json")
        self.assertEqual(r.status_code, 400)

    def test_limpar(self):
        with patch("oink.views.perguntar_ao_oink", return_value="ok"):
            self.post("oi")
        self.client.post(reverse("oink_limpar"))
        self.assertNotIn("historico_oink", self.client.session)

    def test_pagina_abre(self):
        self.assertEqual(self.client.get("/oink/").status_code, 200)


class AcessoTests(TestCase):
    def test_sem_login_chat_nao_funciona(self):
        r = self.client.post(reverse("oink_enviar"), {"mensagem": "oi"}, content_type="application/json")
        self.assertEqual(r.status_code, 401)
        self.assertEqual(self.client.get("/oink/").status_code, 302)
