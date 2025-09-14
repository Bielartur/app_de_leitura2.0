from django.db import models, transaction
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser, PermissionsMixin, BaseUserManager
)

from datetime import date
from typing import Optional
import secrets

def generate_access_key() -> str:
    return secrets.token_hex(16)

class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def get_by_natural_key(self, username):
        # login por e-mail (case-insensitive)
        return self.get(**{f"{self.model.USERNAME_FIELD}__iexact": username})

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email é obrigatório")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser precisa de is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser precisa de is_superuser=True")

        return self.create_user(email, password, **extra_fields)

class Usuario(AbstractBaseUser, PermissionsMixin):  # <— inclui permissões/grupos
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    access_key = models.CharField(
        max_length=32, unique=True, db_index=True, editable=False,
        default=generate_access_key,
        help_text="Chave fixa de 32 caracteres para autenticação por header.",
    )
    meta_anual_paginas = models.PositiveIntegerField(
        default=0, help_text="Meta anual de páginas do usuário."
    )
    meta_mensal_paginas = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Meta mensal padrão. Se vazio, usa meta_anual_paginas/12."
    )

    # Relacionamento com Livro guardando progresso no through
    livros = models.ManyToManyField(
        "livros.Livro",
        through="UserBook",
        through_fields=("usuario", "livro"),  # deixa claro quem é quem
        related_name="leitores",
        blank=True,
    )

    # campos mínimos para admin/auth
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UsuarioManager()  # <— ESSENCIAL

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # sem campos extras obrigatórios no createsuperuser

    def save(self, *args, **kwargs):
        update_fields = kwargs.get("update_fields")
        if self.pk:
            if not update_fields or "access_key" not in update_fields:
                original = type(self).objects.filter(pk=self.pk).values_list("access_key", flat=True).first()
                if original and self.access_key != original:
                    self.access_key = original
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.email

    # ---- Helpers de meta/progresso mensal ----
    @property
    def meta_mensal_efetiva(self) -> int:
        if self.meta_mensal_paginas is not None:
            return int(self.meta_mensal_paginas)
        return self.meta_anual_paginas // 12 if self.meta_anual_paginas else 0

    @staticmethod
    def _month_bounds(d):
        from datetime import date
        from django.utils import timezone
        d = d or timezone.localdate()
        start = d.replace(day=1)
        # início do mês seguinte
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1, day=1)
        else:
            end = start.replace(month=start.month + 1, day=1)
        return start, end

    def paginas_lidas_no_mes(self, mes=None) -> int:
        from django.db.models import Sum
        from django.db.models.functions import Coalesce
        # importe seu model real:
        from livros.models import LeituraDiaria  # ajuste o caminho

        start, end = self._month_bounds(mes)
        return (
            LeituraDiaria.objects
            .filter(usuario=self, dia__gte=start, dia__lt=end)
            .aggregate(total=Coalesce(Sum("paginas_lidas"), 0))
            ["total"]
        )

    def progresso_meta_mensal(self, mes=None, override_meta: int | None = None) -> dict:
        """Retorna dict: {'mes', 'meta', 'lidas', 'restante', 'pct'}."""
        start, _ = self._month_bounds(mes)
        lidas = self.paginas_lidas_no_mes(start)
        meta = override_meta if override_meta is not None else self.meta_mensal_efetiva
        restante = max(0, meta - lidas)
        pct = int(round((lidas / meta) * 100)) if meta else 0
        return {"mes": start, "meta": int(meta), "lidas": int(lidas),
                "restante": int(restante), "pct": pct}

class UserBook(models.Model):
    """
    Liga Usuario <-> Livro, guardando o progresso *do usuário* nesse livro.
    """
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_books"
    )
    livro = models.ForeignKey(
        "livros.Livro", on_delete=models.CASCADE, related_name="user_books"
    )

    pagina_atual = models.PositiveIntegerField(default=0)
    iniciado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    concluido_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = (("usuario", "livro"),)
        indexes = [
            models.Index(fields=["usuario", "livro"]),
        ]

    def __str__(self):
        return f"{self.usuario} ↔ {self.livro}"

    # --- Utilitários de progresso por usuário ---
    @property
    def progresso_pct(self) -> float:
        total = self.livro.total_paginas or 0
        if not total:
            return 0.0
        return round(min(100.0, (self.pagina_atual / total) * 100), 2)

    @property
    def faltam_paginas(self) -> int:
        total = self.livro.total_paginas or 0
        return max(total - (self.pagina_atual or 0), 0)

    @property
    def faltam_pct(self) -> int:
        total = self.livro.total_paginas or 0
        return 0 if not total else int(100 - self.progresso_pct)
    
    @property
    def dias_em_leitura(self) -> int:
        hoje = timezone.now().date()
        data_inicio = self.iniciado_em.date()
        dias_em_leitura = (hoje - data_inicio).days
        return dias_em_leitura

    def _clamp_and_flag_conclusao(self):
        total = self.livro.total_paginas or 0
        self.pagina_atual = min(self.pagina_atual, total)
        if total and self.pagina_atual >= total:
            if not self.concluido_em:
                self.concluido_em = timezone.now()
        else:
            self.concluido_em = None

    def recomputar_de_logs(self):
        """
        Soma LeituraDiaria desse usuário neste livro e atualiza 'pagina_atual'.
        """
        from django.db.models import Sum
        total_user = (
            self.livro.leituras.filter(usuario=self.usuario)
            .aggregate(Sum("paginas_lidas"))["paginas_lidas__sum"]
            or 0
        )
        self.pagina_atual = total_user
        self._clamp_and_flag_conclusao()
        self.save(update_fields=["pagina_atual", "concluido_em", "atualizado_em"])

