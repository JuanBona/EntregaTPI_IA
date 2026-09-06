"""Esquema único del dataset que consume rag/. Ver docs/DISENO.md."""

COLUMNAS = [
    "id",              # hash estable de tipo+titulo+anio, para deduplicar
    "tipo",            # "pelicula" | "libro"
    "titulo",
    "sinopsis",
    "generos",         # string con géneros separados por "|", ej: "thriller|drama"
    "rating",          # float 0-10
    "anio",            # int
    "fuente",          # "tmdb" | "google_books"
    "fuente_id",       # id original en la API de origen, para debug
    "autor_director",  # director (película) o autor (libro)
    "idioma",          # idioma original del contenido, ej: "es", "en"
]


def generar_id(tipo: str, titulo: str, anio) -> str:
    """Hash estable para poder correr la ingesta varias veces sin duplicar filas."""
    import hashlib

    clave = f"{tipo}|{titulo.strip().lower()}|{anio}"
    return hashlib.sha1(clave.encode("utf-8")).hexdigest()[:16]
