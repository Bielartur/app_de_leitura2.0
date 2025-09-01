from django.contrib.auth.decorators import login_required
from django.views.generic import ListView
from livros.models import Livros


class LivroDoneListView(ListView):
    model = Livros                          # modelo a ser listado
    template_name = "livros/livros_concluidos.html"     # template usado
    context_object_name = "livros_concluidos"          # nome da variável no template
    paginate_by = 10                        # paginação automática (10 por página)

    # opcional: personalizar a query
    def get_queryset(self):
        # exemplo: ordenar ou filtrar
        return Livros.objects.order_by("-criado_em")
