# notebook/

`TP_recomendador_grupal.ipynb`: notebook pensado para correr en Google Colab, que
importa los módulos `ingestion/`, `rag/`, `agent/` y `prompts/` y ejecuta el flujo
completo.

## Cómo correrla

1. Abrirla en Colab (o clonar el repo y abrirla en local).
2. Cargar `GOOGLE_API_KEY` y `TMDB_API_KEY` en los Secrets de Colab (ícono de llave).
   En local se leen del `.env`.
3. Ejecutar las celdas en orden. `data/dataset.csv` ya viene en el repo, así que la
   ingesta solo se vuelve a correr si se pone `REGENERAR_DATASET = True`.

## Por qué la lógica vive en `.py`

Los outputs de celda cambian el diff del `.ipynb` aunque el código no cambie, lo que
genera conflictos de merge cuando varias personas lo editan. Por eso el código real está
en módulos que se testean por separado (`tests/`) y la notebook solo los orquesta.
