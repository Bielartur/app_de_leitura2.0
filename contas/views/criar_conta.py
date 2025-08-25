from django.shortcuts import reverse
from django.views.generic import FormView
from contas.forms import CriarContaForm

class CriarConta(FormView):
    template_name = "criarconta.html"
    form_class = CriarContaForm

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('contas:login')
