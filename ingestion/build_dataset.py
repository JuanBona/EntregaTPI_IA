"""Punto de entrada del módulo: trae TMDB + Google Books, limpia y guarda el CSV final.

Uso:
    python -m ingestion.build_dataset
    python -m ingestion.build_dataset --paginas-tmdb 10 --resultados-libros 30
"""

import argparse
import os

from dotenv import load_dotenv

from ingestion.clean import combinar_y_deduplicar, normalizar_libros, normalizar_peliculas
from ingestion.google_books_client import buscar_libros
from ingestion.tmdb_client import buscar_peliculas


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paginas-tmdb", type=int, default=5, help="páginas de 20 películas c/u")
    parser.add_argument("--resultados-libros", type=int, default=20, help="libros por género buscado")
    parser.add_argument(
        "--out",
        default=os.getenv("DATASET_CSV_PATH", "./data/dataset.csv"),
        help="ruta de salida del CSV",
    )
    args = parser.parse_args()

    print(f"Trayendo {args.paginas_tmdb} páginas de TMDB...")
    peliculas_crudas = buscar_peliculas(paginas=args.paginas_tmdb)
    df_peliculas = normalizar_peliculas(peliculas_crudas)
    print(f"  -> {len(df_peliculas)} películas con sinopsis válida")

    print(f"Trayendo {args.resultados_libros} libros por género de Google Books...")
    libros_crudos = buscar_libros(resultados_por_genero=args.resultados_libros)
    df_libros = normalizar_libros(libros_crudos)
    print(f"  -> {len(df_libros)} libros con sinopsis válida")

    df_final = combinar_y_deduplicar(df_peliculas, df_libros)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    df_final.to_csv(args.out, index=False)
    print(f"Dataset guardado en {args.out} ({len(df_final)} filas totales)")


if __name__ == "__main__":
    main()
