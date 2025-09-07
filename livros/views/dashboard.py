from django.views.generic import CreateView
from django.urls import reverse_lazy

from livros.forms import LivroForm


class LivroListView(CreateView):
    form_class = LivroForm
    template_name = "livros/dashboard.html"     # template usado
    context_object_name = "livros"          # nome da variável no template
    success_url = reverse_lazy("livros:dashboard")

    def get_success_url(self):
        return super(LivroListView, self).get_success_url()