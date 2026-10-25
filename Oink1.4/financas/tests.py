import io
import os
import tempfile
from datetime import date
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import User

from contas.testutils import novo_usuario
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from oink import ai

from .models import Transacao
from .resumo import contexto_para_oink


def imagem(tam=(800, 600), formato="PNG"):
    b = io.BytesIO()
    Image.new("RGB", tam, "pink").save(b, formato)
    return b.getvalue()


class ContaTests(TestCase):
    def test_cadastro_loga_e_vai_ao_painel(self):
        r = self.client.post(reverse("cadastro"), {
            "username": "ana", "email": "ana@x.com", "password1": "Senha!Forte123", "password2": "Senha!Forte123", "aceito": "on"})
        self.assertRedirects(r, reverse("index"))

    def test_email_repetido_e_bloqueado(self):
        novo_usuario("a", "ana@x.com", "x")
        r = self.client.post(reverse("cadastro"), {
            "username": "b", "email": "ANA@x.com", "password1": "Senha!Forte123", "password2": "Senha!Forte123", "aceito": "on"})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(User.objects.filter(username="b").exists())

    def test_index_exige_login(self):
        self.assertEqual(self.client.get(reverse("index")).status_code, 302)


class PerfilTests(TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cfg = override_settings(MEDIA_ROOT=self.tmp.name)
        self.cfg.enable()
        self.user = novo_usuario("ana", "ana@x.com", "x")
        self.client.force_login(self.user)

    def tearDown(self):
        self.cfg.disable()
        self.tmp.cleanup()

    def salvar(self, **kw):
        d = {"first_name": "Ana", "email": "ana@x.com"}
        d.update(kw)
        return self.client.post(reverse("perfil"), d)

    def foto(self, nome="f.png", conteudo=None):
        return SimpleUploadedFile(nome, conteudo or imagem(), "image/png")

    def test_foto_vira_quadrado_400(self):
        self.assertRedirects(self.salvar(foto=self.foto()), reverse("perfil"))
        self.user.refresh_from_db()
        self.assertEqual(Image.open(self.user.perfil.foto.path).size, (400, 400))

    def test_trocar_foto_apaga_a_antiga(self):
        self.salvar(foto=self.foto())
        self.salvar(foto=self.foto())
        self.assertEqual(len(os.listdir(os.path.join(self.tmp.name, "perfis"))), 1)

    def test_remover_foto(self):
        self.salvar(foto=self.foto())
        self.salvar(remover_foto="on")
        self.user.refresh_from_db()
        self.assertFalse(self.user.perfil.foto)
        self.assertEqual(os.listdir(os.path.join(self.tmp.name, "perfis")), [])

    def test_recusa_arquivo_que_nao_e_imagem_e_foto_grande(self):
        self.assertEqual(self.salvar(foto=self.foto(conteudo=b"texto")).status_code, 200)
        grande = SimpleUploadedFile("g.png", imagem() + b"0" * (2 * 1024 * 1024), "image/png")
        self.assertEqual(self.salvar(foto=grande).status_code, 200)
        self.assertFalse(getattr(self.user, "perfil", None) and self.user.perfil.foto)

    def test_altera_nome_e_email_e_barra_email_de_outro(self):
        self.salvar(first_name="Aninha", email="nova@x.com")
        self.user.refresh_from_db()
        self.assertEqual((self.user.first_name, self.user.email), ("Aninha", "nova@x.com"))
        novo_usuario("bia", "bia@x.com", "x")
        self.assertEqual(self.salvar(email="BIA@x.com").status_code, 200)

    def test_senha_pode_ser_trocada(self):
        r = self.client.post(reverse("alterar_senha"), {
            "old_password": "x", "new_password1": "Outra!Senha123", "new_password2": "Outra!Senha123"})
        self.assertRedirects(r, reverse("perfil"))

    def test_index_mostra_a_foto(self):
        self.salvar(foto=self.foto())
        self.assertContains(self.client.get(reverse("index")), "/media/perfis/")


class FinancasTests(TestCase):
    def setUp(self):
        self.ana = novo_usuario("ana", password="x")
        self.bia = novo_usuario("bia", password="x")
        self.client.force_login(self.ana)

    def add(self, **kw):
        d = {"tipo": "gasto", "descricao": "Mercado", "valor": "50.00", "categoria": "alimentacao",
             "data": date.today().isoformat()}
        d.update(kw)
        return self.client.post(reverse("index"), d)

    def test_adiciona_e_aparece_no_painel(self):
        self.add(tipo="ganho", valor="2000", categoria="salario", descricao="Salário")
        self.add()
        r = self.client.get(reverse("index"))
        self.assertEqual(r.context["saldo"], 1950)
        self.assertEqual(r.context["categorias"][0]["nome"], "Alimentação")
        self.assertEqual(r.context["categorias"][0]["pct"], 100)

    def test_cpf_na_descricao_e_valor_negativo_sao_recusados(self):
        self.add(descricao="pagar 529.982.247-25")
        self.add(valor="-5")
        self.assertEqual(Transacao.objects.count(), 0)

    def test_nao_exclui_de_outro_usuario(self):
        t = Transacao.objects.create(user=self.bia, tipo="gasto", descricao="x", valor=1, categoria="outros")
        self.assertEqual(self.client.post(reverse("excluir", args=[t.pk])).status_code, 404)

    def test_oink_recebe_so_resumo_do_proprio_usuario(self):
        hoje = date.today()
        Transacao.objects.create(user=self.ana, tipo="gasto", descricao="SEGREDO", valor=80, categoria="lazer", data=hoje)
        Transacao.objects.create(user=self.bia, tipo="gasto", descricao="x", valor=999, categoria="lazer", data=hoje)
        ctx = contexto_para_oink(self.ana)
        self.assertIn("80.00", ctx)
        self.assertNotIn("999", ctx)
        self.assertNotIn("SEGREDO", ctx)
        with patch("oink.views.perguntar_ao_oink", return_value="ok") as ia:
            self.client.post(reverse("oink_enviar"), {"mensagem": "oi"}, content_type="application/json")
            self.assertIn("80.00", ia.call_args[0][1])


class PaginasTests(TestCase):
    def test_paginas_publicas_abrem(self):
        for nome in ("sobre", "pq_usar", "termos", "login", "cadastro"):
            self.assertEqual(self.client.get(reverse(nome)).status_code, 200, nome)

    def test_paginas_logadas_abrem_com_menu_completo(self):
        self.client.force_login(novo_usuario("ana", password="x"))
        for nome in ("index", "chat", "perfil", "alterar_senha", "sobre", "termos", "pq_usar"):
            r = self.client.get(reverse(nome))
            self.assertEqual(r.status_code, 200, nome)
            self.assertContains(r, reverse("chat"))      # "Converse com o Oink" aponta pro chat
            self.assertContains(r, reverse("logout"))    # botão Sair


class TermosEContaTests(TestCase):
    DADOS = {"username": "ana", "email": "ana@x.com", "password1": "Senha!Forte123", "password2": "Senha!Forte123"}

    def test_cadastro_exige_aceitar_os_termos(self):
        dados = {k: v for k, v in self.DADOS.items()}
        dados.pop("aceito", None)
        self.assertEqual(self.client.post(reverse("cadastro"), dados).status_code, 200)
        self.assertFalse(User.objects.filter(username="ana").exists())
        dados["aceito"] = "on"
        self.assertRedirects(self.client.post(reverse("cadastro"), dados), reverse("index"))
        p = User.objects.get(username="ana").perfil
        self.assertTrue(p.aceitou_termos_em)
        self.assertEqual(p.versao_termos, settings.TERMOS_VERSAO)

    def test_quem_nao_aceitou_fica_travado_ate_aceitar(self):
        self.client.force_login(novo_usuario("ana", aceito=False))
        self.assertRedirects(self.client.get(reverse("index")), reverse("aceitar_termos"))
        self.assertRedirects(self.client.get(reverse("chat")), reverse("aceitar_termos"))
        r = self.client.post(reverse("oink_enviar"), {"mensagem": "oi"}, content_type="application/json")
        self.assertEqual(r.status_code, 403)
        self.assertEqual(self.client.get(reverse("termos")).status_code, 200)   # pode ler os termos
        self.client.post(reverse("aceitar_termos"), {})                         # sem marcar: continua travado
        self.assertRedirects(self.client.get(reverse("index")), reverse("aceitar_termos"))
        self.client.post(reverse("aceitar_termos"), {"aceito": "on"})
        self.assertEqual(self.client.get(reverse("index")).status_code, 200)

    def test_versao_nova_dos_termos_pede_aceite_de_novo(self):
        self.client.force_login(novo_usuario("ana"))
        with override_settings(TERMOS_VERSAO="2099-01"):
            self.assertRedirects(self.client.get(reverse("index")), reverse("aceitar_termos"))

    def test_apagar_conta_com_senha_errada_e_certa(self):
        u = novo_usuario("ana", password="segredo")
        Transacao.objects.create(user=u, tipo="gasto", descricao="x", valor=1, categoria="outros")
        self.client.force_login(u)
        self.client.post(reverse("apagar_conta"), {"senha": "errada"})
        self.assertTrue(User.objects.filter(pk=u.pk).exists())
        self.assertRedirects(self.client.post(reverse("apagar_conta"), {"senha": "segredo"}), reverse("login"))
        self.assertFalse(User.objects.filter(pk=u.pk).exists())
        self.assertEqual(Transacao.objects.count(), 0)

    def test_apagar_conta_apaga_a_foto_do_disco(self):
        with tempfile.TemporaryDirectory() as tmp, override_settings(MEDIA_ROOT=tmp):
            u = novo_usuario("ana", "ana@x.com", "segredo")
            self.client.force_login(u)
            self.client.post(reverse("perfil"), {"first_name": "A", "email": "ana@x.com",
                             "foto": SimpleUploadedFile("f.png", imagem(), "image/png")})
            self.assertEqual(len(os.listdir(os.path.join(tmp, "perfis"))), 1)
            self.client.post(reverse("apagar_conta"), {"senha": "segredo"})
            self.assertEqual(os.listdir(os.path.join(tmp, "perfis")), [])

    def test_sair_e_apagar_tem_dialogo_de_confirmacao(self):
        self.client.force_login(novo_usuario("ana"))
        r = self.client.get(reverse("index"))
        self.assertContains(r, 'id="dlg-sair"')
        self.assertContains(r, "data-sair")
        self.assertContains(r, "oink-triste.gif")
        self.assertContains(self.client.get(reverse("perfil")), 'id="dlg-apagar"')

    def test_oink_do_painel_muda_de_humor(self):
        self.client.force_login(novo_usuario("ana"))
        self.assertEqual(self.client.get(reverse("index")).context["humor"], "dormindo")
        self.assertEqual(self.client.get(reverse("index") + "?novo=ganho").context["humor"], "comemorando")
        Transacao.objects.create(user=User.objects.get(username="ana"), tipo="gasto", descricao="x",
                                 valor=50, categoria="lazer", data=date.today())
        self.assertEqual(self.client.get(reverse("index")).context["humor"], "preocupado")


class RecuperarSenhaTests(TestCase):
    def test_pedido_envia_email_com_link_e_a_nova_senha_funciona(self):
        from django.core import mail
        u = novo_usuario("ana", "ana@gmail.com", "Antiga!123")
        r = self.client.post(reverse("password_reset"), {"email": "ANA@gmail.com"})
        self.assertRedirects(r, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["ana@gmail.com"])
        import re
        link = re.search(r"http://testserver(/contas/redefinir/\S+)", mail.outbox[0].body).group(1)
        r = self.client.get(link, follow=True)
        self.assertEqual(r.status_code, 200)
        r = self.client.post(r.request["PATH_INFO"], {"new_password1": "Nova!Senha456", "new_password2": "Nova!Senha456"})
        self.assertRedirects(r, reverse("password_reset_complete"))
        u.refresh_from_db()
        self.assertTrue(u.check_password("Nova!Senha456"))

    def test_email_desconhecido_nao_revela_nada_e_nao_envia(self):
        from django.core import mail
        r = self.client.post(reverse("password_reset"), {"email": "ninguem@x.com"})
        self.assertRedirects(r, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 0)

    def test_link_invalido(self):
        r = self.client.get(reverse("password_reset_confirm", args=["xx", "invalido"]))
        self.assertContains(r, "Link inválido")

    def test_login_tem_esqueci_minha_senha(self):
        self.assertContains(self.client.get(reverse("login")), reverse("password_reset"))


class ConfiguracoesTests(TestCase):
    def setUp(self):
        self.u = novo_usuario("ana", "ana@gmail.com")
        self.client.force_login(self.u)

    def salvar(self, **kw):
        d = {"meta_gastos": "500", "tom_oink": "direto", "usar_dados_no_oink": "on"}
        d.update(kw)
        return self.client.post(reverse("configuracoes"), d)

    def test_salva_preferencias_e_mostra_email_mascarado(self):
        self.assertRedirects(self.salvar(), reverse("configuracoes"))
        p = User.objects.get(pk=self.u.pk).perfil
        self.assertEqual((str(p.meta_gastos), p.tom_oink, p.usar_dados_no_oink), ("500.00", "direto", True))
        self.assertContains(self.client.get(reverse("configuracoes")), "an***@gmail.com")

    def test_meta_aparece_no_painel_e_passar_dela_preocupa(self):
        self.salvar(meta_gastos="100")
        Transacao.objects.create(user=self.u, tipo="gasto", descricao="x", valor=150, categoria="lazer",
                                 data=date.today())
        Transacao.objects.create(user=self.u, tipo="ganho", descricao="y", valor=1000, categoria="salario",
                                 data=date.today())
        r = self.client.get(reverse("index"))
        self.assertEqual((r.context["meta_pct"], r.context["humor"]), (150, "preocupado"))
        self.assertContains(r, "Meta: R$")

    def test_tom_e_privacidade_chegam_na_ia(self):
        Transacao.objects.create(user=self.u, tipo="gasto", descricao="x", valor=80, categoria="lazer",
                                 data=date.today())
        self.salvar(meta_gastos="", tom_oink="direto")
        ctx = contexto_para_oink(User.objects.get(pk=self.u.pk))
        self.assertIn("direta", ctx)
        self.assertIn("80.00", ctx)
        self.salvar(meta_gastos="", usar_dados_no_oink="")          # desmarcou: não envia números
        ctx = contexto_para_oink(User.objects.get(pk=self.u.pk))
        self.assertNotIn("80.00", ctx)
        self.assertIn("NÃO autorizou", ctx)


class AdminOinkTests(TestCase):
    def setUp(self):
        self.adm = novo_usuario("adm", "adm@x.com", aceito=False)     # nem precisa ter aceitado os termos
        self.adm.is_staff = True
        self.adm.save()
        self.comum = novo_usuario("ana")

    def chat(self, **kw):
        d = {"historico": [{"role": "user", "content": "oi"}], "bloquear_cpf": True, "contexto": ""}
        d.update(kw)
        return self.client.post(reverse("adm_chat"), d, content_type="application/json")

    def test_so_staff_entra(self):
        self.assertEqual(self.client.get(reverse("adm_oink")).status_code, 302)    # anônimo -> login
        self.client.force_login(self.comum)
        self.assertEqual(self.client.get(reverse("adm_oink")).status_code, 403)
        self.assertEqual(self.chat().status_code, 403)
        self.client.force_login(self.adm)
        r = self.client.get(reverse("adm_oink"))
        self.assertContains(r, "Tudo liberado")
        self.assertContains(r, "oink-triste.gif")

    def test_chat_de_teste_com_e_sem_bloqueio_de_cpf(self):
        self.client.force_login(self.adm)
        cpf = [{"role": "user", "content": "meu cpf 529.982.247-25"}]
        with patch("oink.adm.ai.perguntar_ao_oink", return_value="ok") as ia:
            self.assertTrue(self.chat(historico=cpf).json()["bloqueado"])
            ia.assert_not_called()
            self.assertEqual(self.chat(historico=cpf, bloquear_cpf=False).json()["resposta"], "ok")
            self.chat(contexto="Gastos: R$ 9,00")
            self.assertIn("R$ 9,00", ia.call_args[0][1])

    def test_admin_ve_o_erro_real_e_historico_invalido(self):
        self.client.force_login(self.adm)
        with patch("oink.adm.ai.perguntar_ao_oink", side_effect=ai.ErroIA("429")):
            r = self.chat()
            self.assertEqual(r.status_code, 502)
            self.assertIn("429", r.json()["erro"])
        self.assertEqual(self.chat(historico=[{"role": "assistant", "content": "x"}]).status_code, 400)

    def test_detector_de_cpf_e_email_de_teste(self):
        from django.core import mail
        self.client.force_login(self.adm)
        post = lambda n, d: self.client.post(reverse(n), d, content_type="application/json")
        self.assertTrue(post("adm_cpf", {"texto": "52998224725"}).json()["bloqueia"])
        self.assertFalse(post("adm_cpf", {"texto": "oi"}).json()["bloqueia"])
        self.assertEqual(post("adm_email", {}).status_code, 200)
        self.assertEqual(mail.outbox[0].to, ["adm@x.com"])

    def test_admin_passa_pelo_bloqueio_dos_termos_e_comum_nao(self):
        self.client.force_login(self.adm)
        self.assertEqual(self.client.get(reverse("index")).status_code, 200)
        self.assertContains(self.client.get(reverse("index")), "Admin Oink")
        self.client.force_login(self.comum)
        self.assertNotContains(self.client.get(reverse("index")), "Admin Oink")

    def test_django_admin_abre_para_staff(self):
        self.adm.is_superuser = True
        self.adm.save()
        self.client.force_login(self.adm)
        self.assertEqual(self.client.get("/admin/").status_code, 200)
