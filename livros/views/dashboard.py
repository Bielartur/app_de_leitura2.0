from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.db import transaction, IntegrityError
from django.db.models.functions import Coalesce
from django.db.models import Sum
from django.utils import timezone
from django.contrib import messages
import logging

from livros.forms import LivroForm
from livros.models import Livro, LeituraDiaria
from contas.models import UserBook  # e opcionalmente UserBookMonthlyGoal se for usar metas
from datetime import timedelta, date as date_cls
from calendar import monthrange


class DashboardView(LoginRequiredMixin, CreateView):
    form_class = LivroForm
    template_name = "livros/dashboard.html"
    success_url = reverse_lazy("livros:dashboard")

    def _month_bounds(d: date_cls | None):
        d = (d or timezone.localdate()).replace(day=1)
        if d.month == 12:
            end = d.replace(year=d.year + 1, month=1, day=1)
        else:
            end = d.replace(month=d.month + 1, day=1)
        return d, end

    # ---------------------- HOOKS CUSTOMIZÁVEIS ----------------------

    def fim_do_mes(self, d: date_cls | None):
        ultimo_dia = monthrange(d.year, d.month)[1]  # 28/29/30/31 conforme o mês
        return d.replace(day=ultimo_dia)

    def form_valid(self, form):
        cd = form.cleaned_data

        # normaliza identificadores únicos (evita "" duplicado)
        isbn = cd.get("isbn") or None
        google_id = cd.get("google_id") or None

        data = {
            "titulo": cd["titulo"],
            "autor": cd["autor"],
            "total_paginas": cd["total_paginas"],
            "categoria": cd.get("categoria"),
            "isbn": isbn,
            "capa_url": cd.get("capa_url") or "",
            "google_id": google_id,
        }

        # mesma prioridade da API: google_id -> isbn -> (titulo, autor, total_paginas)
        if google_id:
            lookup = {"google_id": google_id}
        elif isbn:
            lookup = {"isbn": isbn}
        else:
            lookup = {
                "titulo": data["titulo"],
                "autor": data["autor"],
                "total_paginas": data["total_paginas"],
            }

        with transaction.atomic():
            try:
                obj, created = Livro.objects.get_or_create(**lookup, defaults=data)
            except IntegrityError:
                obj = Livro.objects.get(**lookup)
                created = False

            self.object = obj  # necessário para CreateView


            # cria o vínculo UserBook se ainda não existir (sem mexer em pagina_atual)
            UserBook.objects.get_or_create(
                usuario=self.request.user,
                livro=obj,
            )

        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user_books = (
            self.request.user.user_books
            .filter(concluido_em__isnull=True)
            .select_related("livro", "livro__categoria")
            .only(
                "pagina_atual",
                "livro__id", "livro__titulo", "livro__autor",
                "livro__total_paginas", "livro__categoria", "livro__capa_url",
            )
        )
        context["livros_em_andamento"] = user_books

        user = self.request.user
        hoje = timezone.localdate()
        inicio_mes = hoje.replace(day=1)
        fim_mes = self.fim_do_mes(hoje)

        livros_ativos = user.user_books.filter(concluido_em__isnull=True).count()
        dias_consecutivos = LeituraDiaria.streak_vivo(user) or 0
        # pct_meta_mensal =

        # diário agregado no banco
        agg = (
            LeituraDiaria.objects
            .filter(usuario=user, dia__gte=inicio_mes, dia__lt=fim_mes)
            .values("dia")
            .annotate(total=Coalesce(Sum("paginas_lidas"), 0))
        )
        diario = {row["dia"].isoformat(): int(row["total"]) for row in agg}


        # preenche zeros para todos os dias do mês
        d = inicio_mes
        while d < fim_mes:
            diario.setdefault(d.isoformat(), 0)
            d += timedelta(days=1)

        # ✅ agregue, não sobrescreva
        dashboard = {
            "progresso_meta_mensal": user.progresso_meta_mensal,
            "qtd_livros_ativos": int(livros_ativos),
            "dias_consecutivos": int(dias_consecutivos),
            "diario": dict(sorted(diario.items())),
        }
        # Se já existir algo em context["dashboard"], preserve e atualize:
        context.setdefault("dashboard", {}).update(dashboard)

        return context

    def get_success_url(self):
        return super().get_success_url()
