from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from contas.models import Usuario

class AccessKeyAuthentication(BaseAuthentication):
    """
    Procura a chave em:
    - Header: X-Access-Key: <token>
    - OU Authorization: Key <token>
    """

    keyword = b"Key"

    def authenticate(self, request):
        # 1) X-Access-Key
        key = request.headers.get("X-Access-Key")
        if key:
            return self._authenticate_with_key(key)

        # 2) Authorization: Key <token>
        auth = get_authorization_header(request).split()
        if auth and auth[0].lower() == self.keyword.lower() and len(auth) == 2:
            return self._authenticate_with_key(auth[1].decode())

        return None  # sem credencial -> outras auths podem tentar

    def _authenticate_with_key(self, token: str):
        if not token or len(token) != 32:
            raise AuthenticationFailed("Chave de acesso inválida.")
        try:
            user = Usuario.objects.get(access_key=token)
        except Usuario.DoesNotExist:
            raise AuthenticationFailed("Chave de acesso não reconhecida.")
        return (user, None)
