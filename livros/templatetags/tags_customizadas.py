from django import template

register = template.Library()

@register.filter
def times(n):
    n = int(n or 0)
    return range(max(0, n))

@register.filter
def sub(a, b):
    """Retorna a - b como inteiro, nunca negativo."""
    try:
        return max(0, int(a) - int(b))
    except (TypeError, ValueError):
        return 0

@register.filter
def dotfloat(value, digits=2):
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return ""

@register.simple_tag(takes_context=True)
def userbook(context, livro):
    user = context["request"].user
    return livro.user_books.filter(usuario=user).first()
