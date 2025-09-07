from ninja import Schema, ModelSchema
from livros.models import Livro, Categoria


class CategoriaInSchema(ModelSchema):
    class Config:
        model = Categoria
        model_fields = ('nome',)

class CategoriaOutSchema(ModelSchema):
    class Config:
        model = Categoria
        model_fields = ('id', 'nome',)

class ErrorSchema(Schema):
    error: str

class LivroOutSchema(ModelSchema):
    class Config:
        model = Livro
        model_fields = ('id', 'titulo', 'autor', 'total_paginas', 'pag_atual',
                        'categoria', 'data_inicio', 'isbn', 'capa_url',
                        'google_id') # __all__ para trazer todos os campos, mas não é a melhor prática

class LivroEditSchema(ModelSchema):
    class Config:
        model = Livro
        model_fields = ('pag_atual', 'categoria', 'data_inicio', 'capa_url',)
        model_fields_optional = "__all__"

class LivroCreateSchema(ModelSchema):
    class Config:
        model = Livro
        model_fields = ('titulo', 'autor', 'total_paginas', 'pag_atual', 'categoria', 'data_inicio', 'isbn', 'capa_url', 'google_id')
