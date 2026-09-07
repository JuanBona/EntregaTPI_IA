"""Cliente de la API de Google Books para traer libros.

Docs: https://developers.google.com/books/docs/v1/using
Funciona sin key (rate limit bajo); con GOOGLE_BOOKS_API_KEY en el .env el límite sube.
"""

import os
import time

import requests

GOOGLE_BOOKS_BASE_URL = "https://www.googleapis.com/books/v1/volumes"

# Géneros/temas usados como queries de búsqueda, ya que Google Books no tiene
# un endpoint de "discover por género" como TMDB.
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
            "q": f"subject:{genero}",
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
                if intento == 2:
                    print(f"  Aviso: género '{genero}' falló dos veces ({e}), lo salteo.")
                else:
                    time.sleep(1.0)  # backoff simple antes de reintentar

        time.sleep(0.25)

    return libros