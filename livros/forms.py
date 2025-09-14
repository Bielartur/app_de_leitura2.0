# app/forms.py
from django import forms
from django.core.exceptions import ValidationError
from livros.models import Livro, Categoria


BASE_INPUT = "w-full px-3 py-2 border border-slate-300 rounded-xl focus:ring-2 focus:ring-[var(--great-green)] focus:border-[var(--great-green)] outline-none transition-colors"
class LivroForm(forms.ModelForm):
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.order_by("nome"),
        required=True,                       # torne obrigatório (recomendado)
        label="Categoria",
        widget=forms.Select(attrs={
            "class": BASE_INPUT, "id": "categoria-livro"
        }),
        empty_label="Selecione uma categoria"
    )

    class Meta:
        model = Livro
        fields = [
            "titulo", "autor", "total_paginas", "categoria",
            "isbn", "capa_url", "google_id",
        ]
        labels = {
            "titulo": "Título do Livro *",
            "autor": "Autor *",
            "total_paginas": "Total de Páginas *",
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
            # ocultos / metadados
            "isbn": forms.HiddenInput(attrs={"id": "isbn"}),
            "capa_url": forms.HiddenInput(attrs={"id": "capa-url"}),
            "google_id": forms.HiddenInput(attrs={"id": "google-id"}),
        }

    # validações específicas
    def clean_total_paginas(self):
        total = self.cleaned_data.get("total_paginas")
        if not total or total < 1:
            raise forms.ValidationError("Informe um total de páginas válido (≥ 1).")
        return total

    def validate_unique(self):
        # mantém as outras validações de unicidade do modelo
        exclude = self._get_validation_exclusions()
        try:
            self.instance.validate_unique(exclude=exclude)
        except ValidationError as e:
            # remove APENAS os erros desses campos
            e.error_dict.pop("google_id", None)
            e.error_dict.pop("isbn", None)
            if e.error_dict:
                self._update_errors(e)