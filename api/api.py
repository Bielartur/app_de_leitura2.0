from ninja import NinjaAPI
from livros.models import Categoria, Livro
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.db import IntegrityError
from django.db.models import Q
# from django.forms.models import model_to_dict
from api.schemas import LivroOutSchema, CategoriaOutSchema, CategoriaInSchema, ErrorSchema, \
    LivroEditSchema, LivroCreateSchema

import orjson
from ninja.parser import Parser
from django.http import HttpRequest

class ORJsonParser(Parser):
    def parser_body(self, request):
        return orjson.loads(request.body)
api = NinjaAPI(parser=ORJsonParser(), urls_namespace="api")

@api.exception_handler(Http404)
def not_found_handler(request, exc):
    return api.create_response(
        request,
        {"error": "Elemento não encontrado"},
        status=404
    )

@api.get('categorias/', response=list[CategoriaOutSchema])
def listar_categorias(request):
    categorias = Categoria.objects.all()
    return categorias

@api.get('categoria/{id}/', response=CategoriaOutSchema)
def listar_categoria(request, id: int):
    categoria = get_object_or_404(Categoria, id=id)
    return categoria

@api.post(
    "categoria/create",
    response={
        201: CategoriaOutSchema,   # criado
        400: ErrorSchema          # erro de negócio
    },
)
def criar_categoria(request, payload: CategoriaInSchema):
    try:
        categoria = Categoria.objects.create(nome=payload.nome)
        return 201, categoria
    except IntegrityError:
        return 400, {"error": f"Já existe uma categoria com o nome {payload.nome}"}

@api.put(
    "categoria/create",
    response={
        200: CategoriaOutSchema,   # atualizado
        400: ErrorSchema          # erro de negócio
    },
)
def editar_categoria(request, id: int, payload: CategoriaInSchema):
    try:
        categoria = get_object_or_404(Categoria, id=id)
        categoria.nome = payload.nome if payload.nome else categoria.nome
        categoria.save()
        return 200, categoria
    except IntegrityError:
        return 400, {"error": f"Já existe uma categoria com o nome {payload.nome}"}

@api.delete('categoria/{id}', response=CategoriaOutSchema)
def deletar_categoria(request, id: int):
    categoria = get_object_or_404(Categoria, id=id)
    categoria.delete()

    return categoria

@api.get('livros/', response=list[LivroOutSchema])
def listar_livros(request):
    return Livro.objects.all()

@api.get('livro/{id}', response=LivroOutSchema)
def listar_livro(request, id: int):
    return get_object_or_404(Livro, id=id)

@api.post(
    "livro/create",
    response={201: LivroOutSchema, 200: LivroOutSchema},
)
def criar_livro(request, payload: LivroCreateSchema):
    data = payload.dict()
    data["categoria_id"] = data.pop("categoria")

    lookup = {}
    if data.get("google_id"):
        lookup["google_id"] = data["google_id"]
    elif data.get("isbn"):
        lookup["isbn"] = data["isbn"]
    else:
        lookup = {
            "titulo": data["titulo"],
            "autor": data["autor"],
            "total_paginas": data["total_paginas"],
        }

    try:
        obj, created = Livro.objects.get_or_create(
            **lookup,
            defaults=data,
        )
    except IntegrityError:
        obj = Livro.objects.get(**lookup)
        created = False

    return (201 if created else 200), obj

@api.put('livro/{id}', response=LivroOutSchema)
def editar_livro(request, id: int, payload: LivroEditSchema):
    payload.categoria = get_object_or_404(Categoria, id=payload.categoria)
    livro = get_object_or_404(Livro, id=id)

    livro.pag_atual = payload.pag_atual if payload.pag_atual else livro.pag_atual
    livro.categoria = payload.categoria if payload.categoria else livro.categoria
    livro.capa_url = payload.capa_url if payload.capa_url else livro.capa_url
    livro.data_incio = payload.data_inicio if payload.data_inicio else livro.data_inicio
    livro.save()

    return livro

@api.delete('livro/{id}', response=LivroOutSchema)
def deletar_livro(request, id: int):
    livro = get_object_or_404(Livro, id=id)
    livro.delete()
    return livro

