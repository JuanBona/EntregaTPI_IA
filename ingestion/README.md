# ingestion/

Trae películas (TMDB) y libros (Google Books), los limpia y los guarda en
`data/dataset.csv` con el esquema definido en `schema.py` (ver `docs/DISENO.md`).

## Setup

1. Conseguir una API key de TMDB (gratis): https://www.themoviedb.org/settings/api
2. Completar `TMDB_API_KEY` en tu `.env` (copiado de `.env.example`).
   `GOOGLE_BOOKS_API_KEY` es opcional.

## Correr

```bash
python -m ingestion.build_dataset
```

Opciones:

```bash
python -m ingestion.build_dataset --paginas-tmdb 10 --resultados-libros 30 --out data/dataset.csv
```

## Archivos

- `tmdb_client.py`: pega contra la API de TMDB, trae películas populares con género.
- `google_books_client.py`: pega contra Google Books, busca libros por género/tema.
- `clean.py`: normaliza ambas fuentes al esquema común y deduplica.
- `schema.py`: columnas del dataset final y generador de `id` estable.
- `build_dataset.py`: orquesta todo y escribe `data/dataset.csv`.
- `backfill_datos_faltantes.py`: completa datos que `build_dataset.py` no trae de
  entrada (director de películas, géneros reales de libros), pegando un request extra
  por ítem con el `fuente_id` ya guardado. Ver `docs/DISENO.md` (Dificultades
  encontradas) para el detalle.

## Al terminar

Commitear `data/dataset.csv` (no está en `.gitignore`) para que el resto del equipo
(`/rag`, `/agent`, `/notebook`) pueda trabajar sin necesitar las API keys de TMDB/Google.
