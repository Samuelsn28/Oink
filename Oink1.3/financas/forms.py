from django import forms

from oink.seguranca import contem_cpf

from .models import Transacao


class TransacaoForm(forms.ModelForm):
    class Meta:
        model = Transacao
        fields = ("tipo", "descricao", "valor", "categoria", "data")
        widgets = {"data": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}

    def clean_descricao(self):
        d = self.cleaned_data["descricao"].strip()
        if contem_cpf(d):
            raise forms.ValidationError("Não coloque CPF ou outros dados pessoais na descrição.")
        return d
