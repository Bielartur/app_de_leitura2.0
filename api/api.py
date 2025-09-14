import orjson
from ninja import NinjaAPI, Query
from ninja.parser import Parser
from ninja.errors import HttpError
from ninja.pagination import LimitOffsetPagination, paginate
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.db import IntegrityError, transaction
from django.db.models import Q, F
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from api.services.livros_filters import apply_livro_filters, apply_ordering
from api.utils import get_user
from api.schemas import *

from datetime import timedelta, date as date_cls

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
    "categoria/{id}",
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

class SmallLimitOffset(LimitOffsetPagination):
    default_limit = 20
    max_limit = 100

@api.get("livros/", response=list[LivroOutSchema])
@paginate(SmallLimitOffset)
def listar_livros(request, f: LivrosBaseQuery = Query(...)):
    qs = Livro.objects.all()
    qs = apply_livro_filters(qs, f)
    qs = apply_ordering(qs, f.ordering)
    return qs

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


@api.put(
    "livro/{id}",
    response={
        200: LivroOutSchema,   # atualizado
        400: ErrorSchema          # erro de negócio
    },
)
def editar_livro(request, id: int, payload: LivroEditSchema):
    if payload.categoria:
        payload.categoria = get_object_or_404(Categoria, id=payload.categoria)

    livro = get_object_or_404(Livro, id=id)

    if payload.pag_atual > livro.total_paginas:
        return 400, {"error": "O número de páginas lidas não pode ultrapassar o total de páginas do livro."}

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


@api.get('user/', response={200: UserSchema, 403: ErrorSchema, 404: ErrorSchema})
def listar_usuario(request):
    return get_user(request)


@api.get("user/livros", response=list[LivroOutSchema])
@paginate(SmallLimitOffset)
def livros_do_usuario(request, f: LivrosUserQuery = Query(...)):
    user = get_user(request)

    # base: só livros vinculados ao usuário
    qs = Livro.objects.filter(user_books__usuario=user)

    # status por UserBook (sem perder a forma comum de filtrar/ordenar)
    if f.status == "em_andamento":
        qs = qs.filter(user_books__concluido_em__isnull=True)
    elif f.status == "concluidos":
        qs = qs.filter(user_books__concluido_em__isnull=False)

    # aplica os mesmos filtros de LivrosBaseQuery e ordenação
    qs = apply_livro_filters(qs, f)
    qs = apply_ordering(qs, f.ordering)

    return qs.distinct()  # evita duplicados se houver múltiplos UserBooks


@api.post('user/livro/add_pagina/{livro_id}', response={200: LivroAddPaginaOut, 201: LivroAddPaginaOut, 400: ErrorSchema})
def adicionar_pagina(request, livro_id: int, payload: LivroAddPagina):
    user = get_user(request)
    livro = Livro.objects.get(id=livro_id)

    hoje = timezone.localdate()
    dia_alvo = payload.data_de_leitura or hoje

    # dois modos de input
    delta_in = getattr(payload, "delta_paginas", None)
    pagina_abs = getattr(payload, "pagina_atual", None)
    if delta_in is None and pagina_abs is None:
        raise HttpError(400, "Envie 'delta_paginas' ou 'pagina_atual'.")

    from contas.models import UserBook  # evitar import circular

    with transaction.atomic():
        # bloqueia/garante o UserBook
        ub, _created_ub = UserBook.objects.select_for_update().get_or_create(
            usuario=user, livro=livro, defaults={"pagina_atual": 0}
        )
        atual_anterior = ub.pagina_atual or 0

        # calcula delta (permitindo negativo; regra virá abaixo)
        if delta_in is not None:
            delta = int(delta_in)
        else:
            alvo = max(0, int(pagina_abs))
            delta = alvo - atual_anterior

        # clamp para não ultrapassar o total do livro (apenas se positivo)
        if delta > 0 and getattr(livro, "total_paginas", None) is not None:
            max_delta = max(0, livro.total_paginas - atual_anterior)
            delta = min(delta, max_delta)

        # atualiza/acumula a leitura do dia (unique: usuario+livro+dia)
        leitura = (
            LeituraDiaria.objects
            .select_for_update()
            .filter(usuario=user, livro=livro, dia=dia_alvo)
            .first()
        )

        if leitura is None:
            if delta < 0:
                # não há páginas para reduzir
                raise HttpError(400, "Não há páginas registradas neste dia para reduzir.")
            if delta == 0:
                # nada a fazer, retorna estado atual
                return 200, {"userbook": ub, "leitura_diaria": None}
            # criar registro novo com delta > 0
            leitura = LeituraDiaria(
                usuario=user, livro=livro, dia=dia_alvo, paginas_lidas=delta
            )
            leitura.save()  # dispara hooks
            created_today = True
        else:
            # existe registro; validar negativos
            if delta < 0:
                novo = leitura.paginas_lidas + delta
                if novo < 0:
                    # tentativa de reduzir além do disponível
                    raise HttpError(400, "Redução maior que o registrado para o dia.")
                if novo == 0:
                    # CHECK > 0 impede salvar zero: deletar o registro do dia
                    leitura.delete()
                    ub.refresh_from_db()
                    return 200, {"userbook": ub, "leitura_diaria": None}
                # atualizar com F() para atomicidade + save() para disparar hooks
                leitura.paginas_lidas = F("paginas_lidas") + delta
                leitura.save(update_fields=["paginas_lidas"])
                leitura.refresh_from_db(fields=["paginas_lidas"])
                created_today = False
            else:
                # delta >= 0
                if delta == 0:
                    return 200, {"userbook": ub, "leitura_diaria": leitura}
                leitura.paginas_lidas = F("paginas_lidas") + delta
                leitura.save(update_fields=["paginas_lidas"])
                leitura.refresh_from_db(fields=["paginas_lidas"])
                created_today = False

        # após salvar/deletar, o save() de LeituraDiaria recalculou o UserBook
        ub.refresh_from_db()

    return (201 if created_today else 200), {"userbook": ub, "leitura_diaria": leitura}


def _parse_month(s: str | None) -> date_cls | None:
    if not s:
        return None
    try:
        if len(s) == 7:  # YYYY-MM
            y, m = s.split("-", 1)
            return date_cls(int(y), int(m), 1)
        # YYYY-MM-DD -> normaliza pro 1º dia
        y, m, _ = s.split("-", 2)
        return date_cls(int(y), int(m), 1)
    except Exception:
        raise HttpError(422, "Formato inválido para 'mes'. Use 'YYYY-MM' ou 'YYYY-MM-DD'.")

def _month_bounds(d: date_cls | None):
    d = (d or timezone.localdate()).replace(day=1)
    if d.month == 12:
        end = d.replace(year=d.year + 1, month=1, day=1)
    else:
        end = d.replace(month=d.month + 1, day=1)
    return d, end

@api.get("user/leituras/progresso-mensal", response={200: ProgressoMensalOut})
def progresso_mensal(request, q: ProgressoMensalQuery = Query(None)):
    user = get_user(request)

    mes = _parse_month(q.mes) if q else None
    start, end = _month_bounds(mes)

    # resumo (usa seu helper no Usuario)
    resumo = user.progresso_meta_mensal(mes=start, override_meta=(q.meta if q else None))

    # diário agregado no banco
    agg = (
        LeituraDiaria.objects
        .filter(usuario=user, dia__gte=start, dia__lt=end)
        .values("dia")
        .annotate(total=Coalesce(Sum("paginas_lidas"), 0))
    )
    diario = {row["dia"].isoformat(): int(row["total"]) for row in agg}

    # preenche zeros para todos os dias do mês
    d = start
    while d < end:
        diario.setdefault(d.isoformat(), 0)
        d += timedelta(days=1)

    return {
        "mes": resumo["mes"],        # já vem normalizado como 1º dia
        "meta": resumo["meta"],
        "lidas": resumo["lidas"],
        "restante": resumo["restante"],
        "pct": resumo["pct"],
        "diario": dict(sorted(diario.items())),  # ordena por data (opcional)
    }

@api.post("user/meta/anual", response={200: UserSchema})
def definir_meta_anual(request, payload: MetaAnualIn):
    user = get_user(request)
    user.meta_anual_paginas = payload.meta_anual_paginas
    user.save(update_fields=["meta_anual_paginas"])
    return user

@api.post("user/meta/mensal", response={200: UserSchema})
def definir_meta_mensal(request, payload: MetaMensalIn):
    user = get_user(request)
    user.meta_mensal_paginas = payload.meta_mensal_paginas
    user.save(update_fields=["meta_mensal_paginas"])
    return user

