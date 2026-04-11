# ==============================
# UTIL — FILE UTILS
# ==============================

import re
import unicodedata


def sanitize_filename(nome: str) -> str:
    """
    Sanitiza nome de arquivo para uso seguro no sistema operacional.

    Regras:
    - remove acentos
    - remove caracteres inválidos
    - substitui espaços por underscore
    - limita tamanho
    """

    if not nome:
        return "arquivo"

    # 1. Normaliza acentos (ex: "ação" → "acao")
    nome = unicodedata.normalize('NFKD', nome)
    nome = nome.encode('ascii', 'ignore').decode('ascii')

    # 2. Remove caracteres inválidos
    nome = re.sub(r'[\\/*?:"<>|]', '', nome)

    # 3. Substitui espaços por underscore
    nome = re.sub(r'\s+', '_', nome)

    # 4. Remove caracteres não alfanuméricos (exceto _ e -)
    nome = re.sub(r'[^a-zA-Z0-9_\-]', '', nome)

    # 5. Evita nome vazio
    if not nome:
        nome = "arquivo"

    # 6. Limita tamanho (evita problemas em alguns sistemas)
    return nome[:100]