from livros.templatetags.tags_customizadas import register

VARIANTS = {
    "mes": {
        "bg_color": "indigo-100",
        "text_color": "[var(--mid-blue)]",
        "class_icon": "fa-solid fa-book",
        "label": "Este mês",
        "descricao_qtd": "páginas lidas",
    },
    "sequencia": {
        "bg_color": "cyan-100",
        "text_color": "[var(--great-green)]",
        "class_icon": "fa-solid fa-fire",
        "label": "Sequência",
        "descricao_qtd": "dias consecutivos",
        "texto_positivo": "Mantendo o rítmo",
    },
    "andamento": {
        "bg_color": "violet-100",
        "text_color": "violet-600",
        "class_icon": "fa-regular fa-calendar",
        "label": "Em andamento",
        "descricao_qtd": "livros ativos",
    },
}

@register.inclusion_tag("includes/card.html", takes_context=True)
def dash_card(context, variant, *, qtd, pct_concluida=None, add_livro=False, delay=None):
    """Renderiza um 'includes/card.html' com presets por variant."""
    base = VARIANTS.get(variant, {}).copy()

    # animação: se não veio delay, tenta usar a posição do loop (0.1s, 0.2s, 0.3s…)
    if delay is None:
        fl = context.get("forloop")
        if fl:
            delay = f"{0.1 * (fl.counter)}s"  # 1→0.1s, 2→0.2s...
        else:
            delay = "0.1s"

    base.update({
        "qtd": qtd,
        "pct_concluida": pct_concluida,
        "add_livro": add_livro,
        "animation_delay": delay,
    })
    return base
