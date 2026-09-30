"""Cliente de la API de TMDB (The Movie Database) para traer películas.

Docs: https://developer.themoviedb.org/reference/discover-movie
Necesita TMDB_API_KEY en el .env (gratis, se pide en https://www.themoviedb.org/settings/api).
"""

import os
import time

import requests

TMDB_BASE_URL = "https://api.themoviedb.org/3"


def _api_key() -> str:
    key = os.getenv("TMDB_API_KEY")
    if not key:
        raise RuntimeError(
            "Falta TMDB_API_KEY en el .env. Copiá .env.example a .env y completala."
        )
    return key


def obtener_generos() -> dict[int, str]:
    """Devuelve {id_genero: nombre_genero} para mapear los ids que trae /discover."""
    resp = requests.get(
        f"{TMDB_BASE_URL}/genre/movie/list",
        params={"api_key": _api_key(), "language": "es-AR"},
        timeout=15,
    )
    resp.raise_for_status()
    return {g["id"]: g["name"] for g in resp.json()["genres"]}


def obtener_director(pelicula_id: int) -> str | None:
    """Director(es) de una película, vía /movie/{id}/credits.

    /discover/movie (usado en buscar_peliculas) no trae esta info; hace falta un
    request aparte por película, por eso se llama solo para backfill (ver
    ingestion/backfill_datos_faltantes.py), no en la ingesta masiva.
    """
    resp = requests.get(
        f"{TMDB_BASE_URL}/movie/{pelicula_id}/credits",
        params={"api_key": _api_key()},
        timeout=15,
    )
    resp.raise_for_status()
    directores = [c["name"] for c in resp.json().get("crew", []) if c.get("job") == "Director"]
    return ", ".join(directores) if directores else None


def buscar_peliculas(paginas: int = 5, idioma: str = "es-AR") -> list[dict]:
    """Trae películas populares/mejor rankeadas de TMDB, `paginas` páginas de 20 c/u.

    Devuelve una lista de dicts crudos (formato TMDB), sin normalizar todavía —
    eso lo hace ingestion/clean.py.
    """
    generos = obtener_generos()
    peliculas = []

    for pagina in range(1, paginas + 1):
        resp = requests.get(
            f"{TMDB_BASE_URL}/discover/movie",
            params={
                "api_key": _api_key(),
                "language": idioma,
                "sort_by": "popularity.desc",
                "page": pagina,
                "include_adult": "false",
            },
            timeout=15,
        )
        resp.raise_for_status()
        resultados = resp.json().get("results", [])
        if not resultados:
            break

        for r in resultados:
            r["_generos_nombres"] = [
                generos.get(gid, "desconocido") for gid in r.get("genre_ids", [])
            ]
        peliculas.extend(resultados)

        time.sleep(0.25)  # evita rate limit

    return peliculas
