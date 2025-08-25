from rest_framework.exceptions import AuthenticationFailed, APIException

from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from contas.models import User


class Authentication:
    # ----- Normalização -----
    def _normalize(self, name: str, email: str, password: str) -> tuple[str, str, str]:
        if not name or not name.strip():
            raise APIException('O nome não deve ser nulo')

        if not password or not password.strip():
            raise APIException('A senha não deve ser nula')

        name = name.strip().lower()
        email = self.normalize_email(email)
        hashed_password = make_password(password.strip())
        return name, email, hashed_password

    def normalize_email(self, email: str) -> str:
        if not email:
            raise APIException('O email fornecido é inválido')
        email = email.strip().lower()
        try:
            validate_email(email)
        except ValidationError:
            raise APIException('O email fornecido é inválido')
        return email

    # ----- Signin / Signup -----
    def signin(self, email: str | None = None, password: str | None = None) -> User:
        user = User.objects.filter(email=email).first()
        if not user or not check_password(password or '', user.password):
            raise AuthenticationFailed('Email e/ou senha incorreto(s)')
        return user

    def signup(self, name: str, email: str, password: str) -> User:
        name, email, hashed_password = self._normalize(name, email, password)

        if User.objects.filter(email=email).exists():
            raise APIException('Este email já existe na plataforma')

        created_user = User.objects.create(
            name=name,
            email=email,
            password=hashed_password,
        )
        return created_user
