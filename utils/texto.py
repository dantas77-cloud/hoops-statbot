import re


def limpar(texto):
    """Remove HTML que o modelo às vezes escreve (<br>, <b>...), que apareceria como texto cru no chat."""
    linhas = []
    for l in texto.split("\n"):
        tabela = l.lstrip().startswith("|")
        l = re.sub(r"<br\s*/?>", " · " if tabela else "\n", l, flags=re.I)
        l = re.sub(r"</?(?:b|i|u|strong|em|p|div|span|ul|ol|li|table|tr|td|th)\b[^>]*>", "", l, flags=re.I)
        if tabela:
            l = re.sub(r"\|\s*·\s*", "| ", l)
            l = re.sub(r"\s*·\s*\|", " |", l)
            l = re.sub(r"(?:\s*·){2,}", " ·", l)
        linhas.append(l)
    return "\n".join(linhas)


def resumir(texto, n=800):
    """Mantém começo e fim da mensagem (o veredito costuma ficar no fim)."""
    return texto if len(texto) <= n else texto[: n // 3] + " […] " + texto[-(n - n // 3):]
