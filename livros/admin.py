from django.contrib import admin
from livros.models import Livros, LeituraDiaria

@admin.register(Livros)
class LivrosAdmin(admin.ModelAdmin):
    list_display = ("titulo", "pag_atual", "total_paginas", "progresso_pct", "data_conclusao")
    search_fields = ("titulo",)

@admin.register(LeituraDiaria)
class LeituraDiariaAdmin(admin.ModelAdmin):
    list_display = ("usuario", "livro", "dia", "paginas_lidas", "criado_em")
    list_filter = ("usuario", "livro", "dia")
    search_fields = ("livro__titulo", "usuario__email")
