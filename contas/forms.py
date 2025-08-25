from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django import forms

from contas.models import Usuario

class CriarContaForm(UserCreationForm):
    email = forms.EmailField()

    class Meta(UserCreationForm):
        model = Usuario
        fields = ('name', 'email', 'password1', 'password2')

class EditarPerfilForm(UserChangeForm):
    name = forms.CharField(label='Nome')
    email = forms.EmailField(label='Email')

    class Meta(UserChangeForm):
        model = Usuario
        fields = ('name', 'email')

