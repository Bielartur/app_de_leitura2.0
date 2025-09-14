from contas.models import Usuario
from ninja.errors import HttpError


def get_access_key(request):
    try:
        auth_header = request.headers.get("authorization")
        access_key = auth_header.split(" ")[1] if auth_header else None
    except Exception:
        access_key = None
        
    return access_key


def get_user(request) -> Usuario:
    if request.user.is_authenticated:
        return request.user

    access_key = get_access_key(request)

    if not access_key:
        raise HttpError(403, "Acesso negado: nenhuma chave de acesso foi fornecida no cabeçalho Authorization.")

    user = Usuario.objects.filter(access_key=access_key).first()
    if not user:
        raise HttpError(404, "Usuário não encontrado: a chave de acesso fornecida é inválida ou não está associada a nenhum usuário.")

    return user