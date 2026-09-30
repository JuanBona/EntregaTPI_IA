"""Rankea los candidatos que trajo rag.retriever según qué tan bien le cierran a los 5 perfiles."""

import unicodedata

from agent.perfil import Perfil

PESO_GENERO_FAVORITO = 1.0
PESO_GENERO_NO_BANCADO = -2.0
PESO_TITULO_NO_BANCADO = -3.0
PESO_RATING = 0.1  # rating típico 0-10, así aporta hasta +1 al score
PESO_SEMANTICO = 0.3  # score del retriever es una distancia (más bajo = más parecido)

# El dataset usa los términos de TMDB/Google Books ("Suspense", "Crimen").
_SINONIMOS_GENERO = {
    "thriller": "suspense",
    "policial": "crimen",
}


def _normalizar(texto: str) -> str:
    """Minúsculas y sin tildes: "Ciencia ficción" y "ciencia ficcion" comparan igual."""
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return sin_tildes.lower()


def _normalizar_genero(genero: str) -> str:
    """`_normalizar` más el mapeo de sinónimos entre géneros de libro y de película."""
    normalizado = _normalizar(genero)
    return _SINONIMOS_GENERO.get(normalizado, normalizado)


def _generos_favoritos_para_tipo(perfil: Perfil, tipo: str) -> set[str]:
    generos = (
        perfil.generos_favoritos_peliculas if tipo == "pelicula" else perfil.generos_favoritos_libros
    )
    return {_normalizar_genero(g) for g in generos}


def _titulos_no_bancados(perfil: Perfil) -> set[str]:
    return {_normalizar(item.titulo) for item in perfil.no_banca_titulos}


def _score_candidato(candidato: dict, perfiles: list[Perfil]) -> float:
    generos_candidato = {_normalizar_genero(g) for g in (candidato.get("generos") or "").split("|") if g}
    tipo = candidato.get("tipo")
    titulo = _normalizar(candidato.get("titulo") or "")

    score = 0.0
    for perfil in perfiles:
        favoritos = _generos_favoritos_para_tipo(perfil, tipo)
        score += PESO_GENERO_FAVORITO * len(generos_candidato & favoritos)

        no_bancados = {_normalizar_genero(g) for g in perfil.no_banca_generos}
        score += PESO_GENERO_NO_BANCADO * len(generos_candidato & no_bancados)

        if titulo in _titulos_no_bancados(perfil):
            score += PESO_TITULO_NO_BANCADO

    rating = candidato.get("rating")
    if rating:
        score += PESO_RATING * rating

    distancia_semantica = candidato.get("score")
    if distancia_semantica is not None:
        score -= PESO_SEMANTICO * distancia_semantica

    return score


def rankear_candidatos(candidatos: list[dict], perfiles: list[Perfil]) -> list[dict]:
    """Ordena `candidatos` de mayor a menor afinidad grupal. Agrega la key 'score_grupal'."""
    con_score = []
    for c in candidatos:
        c = {**c, "score_grupal": _score_candidato(c, perfiles)}
        con_score.append(c)

    return sorted(con_score, key=lambda c: c["score_grupal"], reverse=True)
