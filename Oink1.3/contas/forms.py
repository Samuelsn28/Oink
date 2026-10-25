import io

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile
from PIL import Image, ImageOps

from .models import Perfil

LIMITE_FOTO = 2 * 1024 * 1024


class CadastroForm(UserCreationForm):
    email = forms.EmailField(label="E-mail")
    aceito = forms.BooleanField(
        required=True, error_messages={"required": "Você precisa concordar com os Termos de uso para criar a conta."})

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Este e-mail já está cadastrado.")
        return email


class PerfilForm(forms.ModelForm):
    first_name = forms.CharField(label="Nome", max_length=50, required=False)
    email = forms.EmailField(label="E-mail")
    remover_foto = forms.BooleanField(label="Remover minha foto", required=False)

    class Meta:
        model = Perfil
        fields = ("foto",)
        widgets = {"foto": forms.FileInput(attrs={"accept": "image/png,image/jpeg,image/webp", "class": "arquivo-oculto"})}

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self._foto_antiga = self.instance.foto.name if self.instance.pk else ""
        self.fields["first_name"].initial = user.first_name
        self.fields["email"].initial = user.email

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError("Este e-mail já está em uso por outra conta.")
        return email

    def clean_foto(self):
        foto = self.cleaned_data.get("foto")
        if not isinstance(foto, UploadedFile):      # sem foto nova
            return foto
        if foto.size > LIMITE_FOTO:
            raise forms.ValidationError("A foto deve ter no máximo 2 MB.")
        try:
            img = Image.open(foto)
            if img.format not in ("JPEG", "PNG", "WEBP"):
                raise ValueError
            img = ImageOps.fit(ImageOps.exif_transpose(img).convert("RGB"), (400, 400))
        except Exception:
            raise forms.ValidationError("Envie uma imagem JPG, PNG ou WEBP.")
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=85)
        return ContentFile(buf.getvalue(), name=f"{self.user.pk}.jpg")   # sempre quadrada, 400x400

    def clean(self):
        dados = super().clean()
        if dados.get("remover_foto"):
            dados["foto"] = False
        return dados

    def save(self, commit=True):
        perfil = super().save(commit)
        if commit:
            self.user.first_name = self.cleaned_data["first_name"]
            self.user.email = self.cleaned_data["email"]
            self.user.save(update_fields=["first_name", "email"])
            if self._foto_antiga and self._foto_antiga != perfil.foto.name:   # não deixa foto velha sobrando
                perfil.foto.storage.delete(self._foto_antiga)
        return perfil
