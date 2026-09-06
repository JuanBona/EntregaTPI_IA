"""Rankea los candidatos que trajo rag.retriever según qué tan bien le cierran a los 5 perfiles."""

from agent.perfil import Perfil

PESO_GENERO_FAVORITO = 1.0
PESO_GENERO_NO_BANCADO = -2.0
PESO_TITULO_NO_BANCADO = -3.0
PESO_RATING = 0.1  # rating típico 0-10, así aporta hasta +1 al score


def _generos_favoritos_para_tipo(perfil: Perfil, tipo: str) -> set[str]:
    generos = (
        perfil.generos_favoritos_peliculas if tipo == "pelicula" else perfil.generos_favoritos_libros
    )
    return {g.lower() for g in generos}


def _titulos_no_bancados(perfil: Perfil) -> set[str]:
    return {item.titulo.lower() for item in perfil.no_banca_titulos}


def _score_candidato(candidato: dict, perfiles: list[Perfil]) -> float:
    generos_candidato = {g.lower() for g in (candidato.get("generos") or "").split("|") if g}
    tipo = candidato.get("tipo")
    titulo = (candidato.get("titulo") or "").lower()

    score = 0.0
    for perfil in perfiles:
        favoritos = _generos_favoritos_para_tipo(perfil, tipo)
        score += PESO_GENERO_FAVORITO * len(generos_candidato & favoritos)

        no_bancados = {g.lower() for g in perfil.no_banca_generos}
        score += PESO_GENERO_NO_BANCADO * len(generos_candidato & no_bancados)

        if titulo in _titulos_no_bancados(perfil):
            score += PESO_TITULO_NO_BANCADO

    rating = candidato.get("rating")
    if rating:
        score += PESO_RATING * rating

    return score


def rankear_candidatos(candidatos: list[dict], perfiles: list[Perfil]) -> list[dict]:
    """Ordena `candidatos` de mayor a menor afinidad grupal. Agrega la key 'score_grupal'."""
    con_score = []
    for c in candidatos:
        c = {**c, "score_grupal": _score_candidato(c, perfiles)}
        con_score.append(c)

    return sorted(con_score, key=lambda c: c["score_grupal"], reverse=True)
