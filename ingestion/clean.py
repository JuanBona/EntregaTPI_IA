"""Normaliza los datos crudos de TMDB/Google Books al esquema común de ingestion/schema.py."""

import pandas as pd

from ingestion.schema import COLUMNAS, generar_id


def _parsear_anio(fecha: str | None) -> int | None:
    """Extrae el año de una fecha tipo "YYYY-MM-DD" (o similar). None si no es válida."""
    fecha = fecha or ""
    if len(fecha) >= 4 and fecha[:4].isdigit():
        return int(fecha[:4])
    return None


def normalizar_peliculas(peliculas_crudas: list[dict]) -> pd.DataFrame:
    filas = []
    for p in peliculas_crudas:
        sinopsis = (p.get("overview") or "").strip()
        titulo = p.get("title") or p.get("original_title") or ""
        anio = _parsear_anio(p.get("release_date"))

        if not sinopsis or not titulo:
            continue  # sin sinopsis no sirve para el RAG

        filas.append(
            {
                "id": generar_id("pelicula", titulo, anio),
                "tipo": "pelicula",
                "titulo": titulo,
                "sinopsis": sinopsis,
                "generos": "|".join(p.get("_generos_nombres", [])),
                "rating": p.get("vote_average"),
                "anio": anio,
                "fuente": "tmdb",
                "fuente_id": p.get("id"),
                "autor_director": None,  # TMDB /discover no trae director sin otro request
                "idioma": p.get("original_language"),
            }
        )
    return pd.DataFrame(filas, columns=COLUMNAS)


def normalizar_libros(libros_crudos: list[dict]) -> pd.DataFrame:
    filas = []
    for item in libros_crudos:
        info = item.get("volumeInfo", {})
        sinopsis = (info.get("description") or "").strip()
        titulo = info.get("title") or ""

        if not sinopsis or not titulo:
            continue

        anio = _parsear_anio(info.get("publishedDate"))

        autores = info.get("authors") or []

        rating_crudo = info.get("averageRating")
        if pd.notna(rating_crudo):
            rating_normalizado = rating_crudo * 2
        else:
            rating_normalizado = 6.0  # sin rating en Google Books: valor neutro

        filas.append(
            {
                "id": generar_id("libro", titulo, anio),
                "tipo": "libro",
                "titulo": titulo,
                "sinopsis": sinopsis,
                "generos": item.get("_genero_buscado", ""),
                "rating": rating_normalizado,
                "anio": anio,
                "fuente": "google_books",
                "fuente_id": item.get("id"),
                "autor_director": ", ".join(autores) if autores else None,
                "idioma": info.get("language"),
            }
        )
    return pd.DataFrame(filas, columns=COLUMNAS)


def combinar_y_deduplicar(*dataframes: pd.DataFrame) -> pd.DataFrame:
    df = pd.concat(dataframes, ignore_index=True)
    df = df.drop_duplicates(subset="id", keep="first")
    return df.reset_index(drop=True)