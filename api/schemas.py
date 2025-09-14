from ninja import Schema, ModelSchema
from livros.models import Livro, Categoria, LeituraDiaria
from contas.models import Usuario, UserBook
from datetime import datetime, date
from pydantic import Field, model_validator, ConfigDict
from typing import Optional, Literal, Dict

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


class LivroOutSchema(Schema):
    id: int
    titulo: str
    autor: str
    total_paginas: int
    avaliacao: int | None = None
    categoria: CategoriaOutSchema
    isbn: str | None = None
    capa_url: str | None = None
    google_id: str | None = None
    criado_em: datetime
    atualizado_em: datetime
    

class LivroEditSchema(ModelSchema):
    """Schema para UPDATE/PATCH do livro (sem progresso)."""

    class Config:
        model = Livro
        # Quais campos podem ser editados
        model_fields = (
            "titulo",
            "autor",
            "total_paginas",
            "avaliacao",
            "categoria",
            "isbn",
            "capa_url",
            "google_id",
        )
        # Deixe todos opcionais para PATCH
        optional_fields = "__all__"


class LivroCreateSchema(ModelSchema):
    """Schema para criação do livro (dados intrínsecos)."""

    class Config:
        model = Livro
        model_fields = (
            "titulo",
            "autor",
            "total_paginas",
            "avaliacao",
            "categoria",
            "isbn",
            "capa_url",
            "google_id",
        )

class UserBookOut(Schema):
    model_config = ConfigDict(from_attributes=True)
    id: int
    usuario_id: int           # FK como ID (simples pro front)
    livro_id: int             # FK como ID
    pagina_atual: int
    iniciado_em: datetime
    atualizado_em: Optional[datetime] = None
    concluido_em: Optional[datetime] = None

class LeituraDiariaOut(Schema):
    model_config = ConfigDict(from_attributes=True)
    id: int
    usuario_id: int
    livro_id: int
    dia: date
    paginas_lidas: int
    criado_em: datetime
    atualizado_em: datetime

class LivroAddPaginaOut(Schema):
    userbook: UserBookOut
    leitura_diaria: Optional[LeituraDiariaOut] = None   # pode vir None (sem registro no dia)

class LivroAddPagina(Schema):
    data_de_leitura: Optional[date] = Field(
        default=None,
        description="Dia da leitura (default = hoje, timezone do projeto)."
    )
    delta_paginas: Optional[int] = Field(
        default=None, ge=1,
        description="Quantidade a somar ao progresso (ex.: +10)."
    )
    pagina_atual: Optional[int] = Field(
        default=None, ge=0,
        description="Página absoluta atual (ex.: 150)."
    )

    @model_validator(mode="after")
    def _one_of_delta_or_abs(self):
        # Exatamente UM dos campos deve ser enviado
        if (self.delta_paginas is None) == (self.pagina_atual is None):
            raise ValueError("Envie APENAS 'delta_paginas' OU 'pagina_atual'.")
        return self

class LivrosBaseQuery(Schema):
    q: Optional[str] = Field(None, description="Busca por título/autor/editora")
    categoria_id: Optional[int] = None
    autor: Optional[str] = None
    min_paginas: Optional[int] = Field(None, ge=0)
    max_paginas: Optional[int] = Field(None, ge=0)
    ids: Optional[list[int]] = None
    ordering: Literal[
        "titulo","-titulo",
        "autor","-autor",
        "paginas","-paginas",
        "publicado","-publicado",
        "atualizado","-atualizado",
    ] = "-atualizado"

class LivrosUserQuery(LivrosBaseQuery):
    status: Literal["todos","em_andamento","concluidos"] = "todos"  # só para /user/livros


class PaginatedLivrosOut(Schema):
    count: int
    limit: int
    offset: int
    results: list["LivroOutSchema"]  # já existente no seu projeto

class UserSchema(ModelSchema):

    class Config:
        model = Usuario
        model_fields = ('id', 'name', 'email', 'access_key', 'meta_anual_paginas', 'meta_mensal_paginas', 'livros')

class UserBookSchema(ModelSchema):
    
    class Config:
        model = UserBook
        model_fields = '__all__'

class MetaAnualIn(Schema):
    meta_anual_paginas: int = Field(ge=0)

class MetaMensalIn(Schema):
    # permita None para "limpar" e voltar a usar anual/12, se quiser
    meta_mensal_paginas: int | None = Field(default=None, ge=0)

class ProgressoMensalQuery(Schema):
    mes: Optional[str] = Field(
        default=None,
        description="Mês alvo. Aceita 'YYYY-MM' ou 'YYYY-MM-DD'. Se omitido, usa o mês atual."
    )
    meta: Optional[int] = Field(default=None, ge=0, description="Override da meta mensal para o cálculo.")

class ProgressoMensalOut(Schema):
    mes: date            # sempre 1º dia do mês
    meta: int
    lidas: int
    restante: int
    pct: int
    diario: Dict[str, int]  # {"2025-09-01": 12, "2025-09-02": 0, ...}