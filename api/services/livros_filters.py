# api/services/livros_filters.py
from django.db.models import Q
from livros.models import Livro  # ajuste o caminho

ORDER_MAP = {
    "titulo": "titulo",
    "-titulo": "-titulo",
    "autor": "autor",
    "-autor": "-autor",
    "paginas": "total_paginas",
    "-paginas": "-total_paginas",
    "publicado": "publicado_em",      # ajuste pro nome real
    "-publicado": "-publicado_em",
    "atualizado": "atualizado_em",    # ajuste pro nome real
    "-atualizado": "-atualizado_em",
}

def apply_livro_filters(qs, f) -> "Livro.objects.none().__class__":
    """Aplica filtros comuns de LivrosBaseQuery a um QS de Livro."""
    if f.q:
        qs = qs.filter(
            Q(titulo__icontains=f.q) |
            Q(autor__icontains=f.q) |
            Q(editora__icontains=f.q)
        )
    if f.categoria_id is not None:
        qs = qs.filter(categoria_id=f.categoria_id)
    if f.autor:
        qs = qs.filter(autor__icontains=f.autor)
    if f.min_paginas is not None:
        qs = qs.filter(total_paginas__gte=f.min_paginas)
    if f.max_paginas is not None:
        qs = qs.filter(total_paginas__lte=f.max_paginas)
    if f.ids:
        qs = qs.filter(id__in=f.ids)
    return qs

def apply_ordering(qs, ordering: str):
    return qs.order_by(ORDER_MAP.get(ordering, "-atualizado_em"))
