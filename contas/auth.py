from rest_framework.exceptions import AuthenticationFailed, APIException

from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from contas.models import User


class Authentication:

    def _normalize(name, email, password) -> tuple[str]:
        if not name.strip():
            raise APIException('O nome não deve ser nulo')

        if not password.strip():
            raise APIException('A senha não deve ser nula')

        name = name.strip().lower()
        email = Authentication.normalize_email(email)
        hashed_password = make_password(password.strip())

        return name, email, hashed_password
    
    def normalize_email(email):
        email = email.strip().lower()     
        try:
            validate_email(email)

        except ValidationError:
            raise APIException('O email fornecido é inválido')
        
        return email

    def signin(self, email=None, password=None) -> User:
        user = User.objects.filter(email=email).first()

        if not user or not check_password(password, user.password):
            raise AuthenticationFailed('Email e/ou senha incorreto(s)')
        
        return user
    
    def signup(self, name, email, password):        
        name, email, hashed_password = self._normalize(name, email, password)

        if User.objects.filter(email=email).exists():
            raise APIException('Este email já existe na plataforma')
        
        created_user = User.objects.create(
            name=name,
            email=email,
            password=hashed_password,
        )

        return created_user
