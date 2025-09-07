# app/forms.py
from django import forms
from livros.models import Livro, Categoria

BASE_INPUT = "w-full px-3 py-2 border border-slate-300 rounded-xl focus:ring-2 focus:ring-[var(--great-green)] focus:border-[var(--great-green)] outline-none transition-colors"

class LivroForm(forms.ModelForm):
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.order_by("nome"),
        required=False,  # mude para True se for obrigatório
        label="Categoria",
        widget=forms.Select(attrs={
            "class": BASE_INPUT, "id": "categoria-livro"
        }),
        empty_label="Selecione uma categoria"
    )

    class Meta:
        model = Livro
        fields = [
            "titulo", "autor", "total_paginas", "pag_atual", "categoria",
            "data_inicio", "isbn", "capa_url", "google_id"
        ]
        labels = {
            "titulo": "Título do Livro *",
            "autor": "Autor *",
            "total_paginas": "Total de Páginas *",
            "pag_atual": "Página Atual",
            "data_inicio": "Data de Início",
        }
        widgets = {
            "titulo": forms.TextInput(attrs={
                "placeholder": "Ex: O Poder do Hábito",
                "class": BASE_INPUT, "id": "titulo-livro", "required": True
            }),
            "autor": forms.TextInput(attrs={
                "placeholder": "Ex: Charles Duhigg",
                "class": BASE_INPUT, "id": "autor-livro", "required": True
            }),
            "total_paginas": forms.NumberInput(attrs={
                "placeholder": "408", "min": 1,
                "class": BASE_INPUT, "id": "total-paginas", "required": True
            }),
            "pag_atual": forms.NumberInput(attrs={
                "placeholder": "0", "min": 0,
                "class": BASE_INPUT, "id": "pagina-atual"
            }),
            "data_inicio": forms.DateInput(attrs={
                "type": "date",
                "class": BASE_INPUT, "id": "data-inicio"
            }),
            # ocultos / metadados
            "isbn": forms.HiddenInput(attrs={"id": "isbn"}),
            "capa_url": forms.HiddenInput(attrs={"id": "capa-url"}),
            "google_id": forms.HiddenInput(attrs={"id": "google-id"}),
        }

    def clean(self):
        data = super().clean()
        total = data.get("total_paginas") or 0
        atual = data.get("pag_atual") or 0
        if atual > total:
            self.add_error("pag_atual", "Página atual não pode ser maior que o total de páginas.")
        return data