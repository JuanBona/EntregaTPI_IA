"""Completa datos que quedaron incompletos en la primera corrida de la ingesta
(ver docs/DISENO.md, sección "Dificultades encontradas").

- Películas: TMDB /discover/movie no trae director, hace falta /movie/{id}/credits.
- Libros: Google Books solo etiqueta cada libro con el género de búsqueda que lo
  trajo, no con sus categorías reales (volumeInfo.categories).

Usa el `fuente_id` ya guardado en el dataset para pedir un dato extra por ítem, sin
tener que volver a correr toda la ingesta (que reharía las búsquedas y podría traer
películas/libros distintos a los ya commiteados).

Uso: python -m ingestion.backfill_datos_faltantes
"""

import os
import time

import pandas as pd
from dotenv import load_dotenv

from ingestion.google_books_client import obtener_categorias
from ingestion.tmdb_client import obtener_director


def main() -> None:
    load_dotenv()
    csv_path = os.getenv("DATASET_CSV_PATH", "./data/dataset.csv")
    df = pd.read_csv(csv_path)

    peliculas_sin_director = df[(df["tipo"] == "pelicula") & df["autor_director"].isna()]
    if not os.getenv("TMDB_API_KEY"):
        print("Sin TMDB_API_KEY en el .env: salteo el backfill de directores.")
    else:
        print(f"Buscando director para {len(peliculas_sin_director)} películas...")
        encontrados = 0
        for idx, fila in peliculas_sin_director.iterrows():
            try:
                director = obtener_director(int(fila["fuente_id"]))
            except Exception as e:
                print(f"  aviso: no se pudo traer el director de '{fila['titulo']}' ({e})")
                director = None
            if director:
                df.at[idx, "autor_director"] = director
                encontrados += 1
            time.sleep(0.25)
        print(f"  -> {encontrados}/{len(peliculas_sin_director)} películas con director encontrado")

    libros = df[df["tipo"] == "libro"]
    if not os.getenv("GOOGLE_BOOKS_API_KEY"):
        print(
            "Sin GOOGLE_BOOKS_API_KEY en el .env: salteo el backfill de géneros de "
            "libros (sin key, Google Books rate-limita tan fuerte que ni con reintentos "
            "responde; ver docs/DISENO.md, sección Dificultades encontradas)."
        )
    else:
        print(f"Buscando categorías reales para {len(libros)} libros...")
        agregados = 0
        for idx, fila in libros.iterrows():
            try:
                categorias = obtener_categorias(fila["fuente_id"])
            except Exception as e:
                print(f"  aviso: no se pudieron traer categorías de '{fila['titulo']}' ({e})")
                categorias = []
            generos_actuales = [g for g in str(fila["generos"]).split("|") if g]
            generos_nuevos = generos_actuales + [g for g in categorias if g not in generos_actuales]
            if len(generos_nuevos) > len(generos_actuales):
                df.at[idx, "generos"] = "|".join(generos_nuevos)
                agregados += 1
            time.sleep(1.5)
        print(f"  -> {agregados}/{len(libros)} libros con un género extra")

    df.to_csv(csv_path, index=False)
    print(f"Dataset actualizado en {csv_path}")


if __name__ == "__main__":
    main()
