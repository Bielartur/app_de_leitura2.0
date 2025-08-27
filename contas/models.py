from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser, PermissionsMixin, BaseUserManager
)
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
