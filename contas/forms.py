from django.contrib.auth.forms import UserChangeForm, UserCreationForm, AuthenticationForm
from django import forms

from contas.models import Usuario

class CriarContaForm(UserCreationForm):
    name = forms.CharField(label='Nome')
    email = forms.EmailField(label='Email')

    class Meta(UserCreationForm):
        model = Usuario
        fields = ('name', 'email', 'password1', 'password2')

class EditarPerfilForm(UserChangeForm):
    name = forms.CharField(label='Nome')
    email = forms.EmailField(label='Email')

    class Meta(UserChangeForm):
        model = Usuario
        fields = ('name', 'email')

class LoginForm(AuthenticationForm):
    remember_me = forms.BooleanField(
        required=False, initial=True, label="Lembrar de mim"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # melhora autofill
        self.fields["username"].widget.attrs.update({"autocomplete": "username"})
        self.fields["password"].widget.attrs.update({"autocomplete": "current-password"})
