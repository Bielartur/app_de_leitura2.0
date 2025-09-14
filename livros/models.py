from django.db import models, transaction
from django.db.models import Sum, Q
from django.utils import timezone
from django.conf import settings

from datetime import timedelta


class Categoria(models.Model):
    nome = models.CharField("Nome", max_length=100, unique=True)

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

    def __str__(self):
        return self.nome


class Livro(models.Model):
    class Avaliacao(models.IntegerChoices):
        PESSIMO = 1, "Péssimo"
        RUIM = 2, "Ruim"
        REGULAR = 3, "Regular"
        BOM = 4, "Bom"
        OTIMO = 5, "Ótimo"

    # --- apenas atributos do livro (sem variáveis por usuário) ---
    titulo = models.CharField(max_length=100)
    autor = models.CharField("Autor", max_length=100)
    total_paginas = models.PositiveIntegerField()
    avaliacao = models.IntegerField(choices=Avaliacao.choices, null=True, blank=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, default=1)
    capa_url = models.URLField("URL Imagem", null=True, blank=True)
    isbn = models.CharField(max_length=32, null=True, blank=True, unique=True)
    google_id = models.CharField(max_length=32, null=True, blank=True, unique=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.titulo} - {self.autor}"

    # --- conveniências dependentes do usuário (usando o through UserBook) ---
    def userbook(self, usuario):
        """Retorna o vínculo Usuario<->Livro (UserBook) ou None."""
        return self.user_books.filter(usuario=usuario).first()

    def progresso_pct_para(self, usuario) -> float:
        """% lido por um usuário específico (0–100)."""
        ub = self.userbook(usuario)
        if not ub or not self.total_paginas:
            return 0.0
        return round(min(100.0, (ub.pagina_atual / self.total_paginas) * 100), 2)

    def faltam_paginas_para(self, usuario) -> int:
        """Páginas restantes para um usuário específico."""
        ub = self.userbook(usuario)
        lidas = ub.pagina_atual if ub else 0
        return max((self.total_paginas or 0) - lidas, 0)

    def faltam_pct_para(self, usuario) -> int:
        """% restante para um usuário específico (0–100)."""
        pct = self.progresso_pct_para(usuario)
        return int(100 - pct)


class LeituraDiaria(models.Model):
    """
    Registro do quanto foi lido em um determinado DIA.
    """
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="leituras",
    )
    livro = models.ForeignKey(
        "Livro",
        on_delete=models.CASCADE,
        related_name="leituras",
    )
    dia = models.DateField(db_index=True, default=timezone.localdate)
    paginas_lidas = models.PositiveIntegerField(default=0)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "livro", "dia"],
                name="unique_leitura_por_usuario_livro_dia",
            ),
            models.CheckConstraint(
                check=Q(paginas_lidas__gte=0),
                name="leit_diaria_paginas_gte_zero",  # mude o nome para forçar a migração
            ),
        ]
        indexes = [models.Index(fields=["usuario", "dia"])]
        ordering = ["-dia"]

    def __str__(self):
        return f"{self.usuario} | {self.livro} | {self.dia} (+{self.paginas_lidas} págs)"

    # -------------------- STREAKS (dias consecutivos) --------------------
    @classmethod
    def _dias_lidos_set(cls, usuario, ate=None) -> set:
        """
        Retorna um set com todas as datas (YYYY-MM-DD) em que o usuário leu,
        até a data 'ate' (inclusiva).
        """
        ate = ate or timezone.localdate()
        return set(
            cls.objects
            .filter(usuario=usuario, dia__lte=ate)
            .values_list("dia", flat=True)
            .distinct()
        )

    @classmethod
    def streak_atual(cls, usuario, ate=None) -> int:
        """
        Conta dias consecutivos de leitura até 'ate' (default = hoje).
        Se hoje não leu, retorna 0.
        """
        ate = ate or timezone.localdate()
        dias = cls._dias_lidos_set(usuario, ate=ate)

        streak = 0
        d = ate
        while d in dias:
            streak += 1
            d = d - timedelta(days=1)
        return streak

    @classmethod
    def streak_vivo(cls, usuario) -> int:
        """
        Conta streak 'vivo': se hoje não leu, conta até ontem.
        """
        hoje = timezone.localdate()
        leu_hoje = cls.objects.filter(usuario=usuario, dia=hoje).exists()
        limite = hoje if leu_hoje else (hoje - timedelta(days=1))
        return cls.streak_atual(usuario, ate=limite)
    # --------------------------------------------------------------------

    def aplicar_no_progresso(self):
        """
        Recalcula o progresso do *usuário* neste livro e atualiza UserBook.
        """
        from contas.models import UserBook  # evite import circular se estiver no mesmo arquivo

        with transaction.atomic():
            ub, _ = UserBook.objects.select_for_update().get_or_create(
                usuario=self.usuario,
                livro=self.livro,
            )

            total_user = (
                LeituraDiaria.objects.filter(usuario=self.usuario, livro=self.livro)
                .aggregate(total=Sum("paginas_lidas"))["total"]
                or 0
            )

            ub.pagina_atual = total_user
            ub._clamp_and_flag_conclusao()
            ub.save(update_fields=["pagina_atual", "concluido_em", "atualizado_em"])

    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)
            self.aplicar_no_progresso()

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            usuario = self.usuario
            livro = self.livro
            super().delete(*args, **kwargs)
            self.usuario = usuario
            self.livro = livro
            self.aplicar_no_progresso()
