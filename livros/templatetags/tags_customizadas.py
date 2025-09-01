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
