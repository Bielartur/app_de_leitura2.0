from django.db import models
from django.contrib.auth.models import AbstractBaseUser
import secrets

def generate_access_key() -> str:
    # 32 caracteres hexadecimais (0-9a-f)
    return secrets.token_hex(16)  # 16 bytes -> 32 chars

class Usuario(AbstractBaseUser):
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    access_key = models.CharField(
        max_length=32,
        unique=True,
        db_index=True,
        editable=False,
        default=generate_access_key,
        help_text="Chave fixa de 32 caracteres para autenticação por header.",
    )

    def save(self, *args, **kwargs):
        update_fields = kwargs.get("update_fields")
        if self.pk:
            # Se NÃO estamos atualizando explicitamente a access_key,
            # impeça alterações (protege contra edições acidentais)
            if not update_fields or "access_key" not in update_fields:
                original = type(self).objects.filter(pk=self.pk).values_list("access_key", flat=True).first()
                if original and self.access_key != original:
                    self.access_key = original
        return super().save(*args, **kwargs)

    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.email
