from django.shortcuts import reverse
from django.views.generic import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from contas.models import Usuario
from contas.forms import EditarPerfilForm

class EditarPerfil(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    template_name = "editarperfil.html"
    form_class = EditarPerfilForm
    model = Usuario

    def test_func(self):
        user = self.get_object()
        return self.request.user == user

    def get_success_url(self):
        return reverse('contas/editar_perfil')