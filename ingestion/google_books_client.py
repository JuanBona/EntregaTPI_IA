"""Cliente de la API de Google Books para traer libros.

Docs: https://developers.google.com/books/docs/v1/using
Funciona sin key (rate limit bajo); con GOOGLE_BOOKS_API_KEY en el .env el límite sube.
"""

import os
import time

import requests

GOOGLE_BOOKS_BASE_URL = "https://www.googleapis.com/books/v1/volumes"

# Géneros/temas usados como queries de búsqueda, ya que Google Books no tiene
# un endpoint de "discover por género" como TMDB. Se mantienen en español porque
# así quedan etiquetados los libros en el dataset (consistente con los géneros de TMDB).
GENEROS_BUSQUEDA = [
    "ficción",
    "ciencia ficción",
    "fantasía",
    "misterio",
    "thriller",
    "romance",
    "biografía",
    "historia",
    "terror",
    "poesía",
]

# El subject metadata de Google Books está mayormente en inglés (BISAC/LCSH), así
# que traducimos el género antes de armar la query para no perder resultados.
_TRADUCCION_GENERO_BUSQUEDA = {
    "ficción": "fiction",
    "ciencia ficción": "science fiction",
    "fantasía": "fantasy",
    "misterio": "mystery",
    "thriller": "thriller",
    "romance": "romance",
    "biografía": "biography",
    "historia": "history",
    "terror": "horror",
    "poesía": "poetry",
}


def _termino_busqueda(genero: str) -> str:
    """Traduce `genero` (español) al término en inglés que usa Google Books como subject."""
    return _TRADUCCION_GENERO_BUSQUEDA.get(genero, genero)


_CATEGORIA_A_GENERO = {ingles: espanol for espanol, ingles in _TRADUCCION_GENERO_BUSQUEDA.items()}


def obtener_categorias(volumen_id: str) -> list[str]:
    """Géneros reales de un libro (además del que lo trajo por búsqueda), vía
    GET /volumes/{id}, traducidos a los géneros conocidos del dataset.

    volumeInfo.categories de Google Books viene en inglés y con formato libre (ej.
    "Fiction / Mystery & Detective"), así que solo se toman las categorías que
    contienen alguno de los términos de _TRADUCCION_GENERO_BUSQUEDA; el resto se
    descarta para no meter géneros que agent/ranking.py no sabría comparar.

    Sin GOOGLE_BOOKS_API_KEY el rate limit es bajo y aparecen 429 seguido si se pega
    muy rápido; se reintenta con backoff antes de darse por vencido con este libro.
    """
    api_key = os.getenv("GOOGLE_BOOKS_API_KEY")
    params = {"key": api_key} if api_key else None

    resp = None
    for intento, espera in enumerate((0, 3, 8), start=1):
        if espera:
            time.sleep(espera)
        resp = requests.get(f"{GOOGLE_BOOKS_BASE_URL}/{volumen_id}", params=params, timeout=15)
        if resp.status_code != 429:
            break
    resp.raise_for_status()
    categorias_crudas = resp.json().get("volumeInfo", {}).get("categories", [])

    generos = []
    for categoria in categorias_crudas:
        categoria_lower = categoria.lower()
        for termino_en, genero_es in _CATEGORIA_A_GENERO.items():
            if termino_en in categoria_lower and genero_es not in generos:
                generos.append(genero_es)
    return generos


def buscar_libros(generos: list[str] | None = None, resultados_por_genero: int = 20) -> list[dict]:
    """Busca libros por género/tema. Devuelve dicts crudos (formato Google Books).

    Si un género falla (rate limit, error transitorio de Google, etc.), se
    reintenta una vez y si vuelve a fallar se lo saltea, sin perder los libros
    ya traídos de los géneros anteriores.
    """
    generos = generos or GENEROS_BUSQUEDA
    api_key = os.getenv("GOOGLE_BOOKS_API_KEY")  # opcional
    libros = []

    for genero in generos:
        params = {
            "q": f"subject:{_termino_busqueda(genero)}",
            "maxResults": min(resultados_por_genero, 40),  # 40 es el máximo de la API
            "langRestrict": "es",
        }
        if api_key:
            params["key"] = api_key

        for intento in (1, 2):
            try:
                resp = requests.get(GOOGLE_BOOKS_BASE_URL, params=params, timeout=15)
                resp.raise_for_status()
                items = resp.json().get("items", [])
                for item in items:
                    item["_genero_buscado"] = genero
                libros.extend(items)
                break
            except requests.exceptions.RequestException as e:
                mensaje = str(e).replace(api_key, "***") if api_key else str(e)
                if intento == 2:
                    print(f"  Aviso: género '{genero}' falló dos veces ({mensaje}), lo salteo.")
                else:
                    time.sleep(1.0)  # backoff simple antes de reintentar

        time.sleep(0.25)

    return libros