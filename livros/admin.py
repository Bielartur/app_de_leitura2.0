from django.contrib import admin
from livros.models import Livro, LeituraDiaria, Categoria


@admin.register(Livro)
class LivrosAdmin(admin.ModelAdmin):
    list_display = ("titulo", "pag_atual", "total_paginas", "progresso_pct", "data_conclusao")
    search_fields = ("titulo",)

@admin.register(LeituraDiaria)
class LeituraDiariaAdmin(admin.ModelAdmin):
    list_display = ("usuario", "livro", "dia", "paginas_lidas", "criado_em")
    list_filter = ("usuario", "livro", "dia")
    search_fields = ("livro__titulo", "usuario__email")

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nome",)
    list_filter = ("livro",)
    search_fields = ("livro__titulo", "usuario__email")