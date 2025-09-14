from django.contrib import admin
from livros.models import Livro, LeituraDiaria, Categoria


@admin.register(Livro)
class LivroAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "titulo",
        "autor",
        "total_paginas",
        "categoria",
        "avaliacao",
        "atualizado_em",
    )
    search_fields = ("titulo", "autor", "isbn", "google_id")
    list_filter = ("categoria", "avaliacao")
    ordering = ("titulo",)


@admin.register(LeituraDiaria)
class LeituraDiariaAdmin(admin.ModelAdmin):
    list_display = ("usuario", "livro", "dia", "paginas_lidas", "criado_em")
    list_filter = ("usuario", "livro", "dia")
    search_fields = ("livro__titulo", "usuario__email")
    ordering = ("-dia",)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("id", "nome", "qtd_livros")
    search_fields = ("nome",)

    def qtd_livros(self, obj):
        # Reverse default: Livro.categoria -> obj.livro_set
        return obj.livro_set.count()
    qtd_livros.short_description = "Livros"
