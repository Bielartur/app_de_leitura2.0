# models.py
from django.db import models, transaction
from django.utils import timezone
from django.conf import settings

class Categoria(models.Model):
    nome = models.CharField("Nome", max_length=100, unique=True)

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

    def __str__(self):
        return self.nome

class Livros(models.Model):
    class Avaliacao(models.IntegerChoices):
        PESSIMO = 1, "Péssimo"
        RUIM = 2, "Ruim"
        REGULAR = 3, "Regular"
        BOM = 4, "Bom"
        OTIMO = 5, "Ótimo"

    titulo = models.CharField(max_length=100)
    pag_atual = models.PositiveIntegerField(default=0)
    total_paginas = models.PositiveIntegerField(null=False, blank=False)
    avaliacao = models.IntegerField(
        choices=Avaliacao.choices,
        default=Avaliacao.REGULAR,
    )
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    data_conclusao = models.DateTimeField(null=True, blank=True)

    @property
    def progresso_pct(self) -> float:
        if not self.total_paginas:
            return 0.0
        return min(100.0, (self.pag_atual / self.total_paginas) * 100)

    def __str__(self):
        return f"{self.titulo} ({self.avaliacao}/5)"


class LeituraDiaria(models.Model):
    """
    Registro do quanto foi lido em um determinado DIA.
    """
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="leituras"
    )
    livro = models.ForeignKey(
        Livros,
        on_delete=models.CASCADE,
        related_name="leituras"
    )
    dia = models.DateField(db_index=True)  # usa DateField para consolidar por dia
    paginas_lidas = models.PositiveIntegerField()  # quantas páginas foram lidas nesse dia
    observacao = models.CharField(max_length=200, blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        # um registro por dia por livro/usuário (evita duplicação acidental)
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "livro", "dia"],
                name="unique_leitura_por_usuario_livro_dia"
            )
        ]
        ordering = ["-dia"]

    def __str__(self):
        return f"{self.usuario} | {self.livro} | {self.dia} (+{self.paginas_lidas} págs)"

    def aplicar_no_livro(self):
        """
        Aplica o efeito desta leitura no progresso do livro (pag_atual/data_conclusao).
        Chame isso ao criar/atualizar/excluir logs, mantendo consistência.
        """
        livro = self.livro
        # Recalcula pag_atual somando todas as leituras do livro (mais seguro)
        total = self.livro.leituras.aggregate(models.Sum("paginas_lidas"))["paginas_lidas__sum"] or 0
        livro.pag_atual = min(total, livro.total_paginas)

        # Marca conclusão quando alcançar o total
        if livro.pag_atual >= livro.total_paginas and not livro.data_conclusao:
            livro.data_conclusao = timezone.now()
        elif livro.pag_atual < livro.total_paginas and livro.data_conclusao:
            # se “desfez” alguma leitura, retira conclusão
            livro.data_conclusao = None

        livro.save(update_fields=["pag_atual", "data_conclusao", "atualizado_em"])

    def save(self, *args, **kwargs):
        with transaction.atomic():
            creating = self._state.adding
            super().save(*args, **kwargs)
            # Reaplica progresso sempre que salvar (create/update)
            self.aplicar_no_livro()

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            super().delete(*args, **kwargs)
            # Reaplica progresso após excluir
            self.aplicar_no_livro()
