# notebook/

El entregable final del TP: `TP_recomendador_grupal.ipynb`, pensado para correr en
Google Colab, integrando los 4 módulos anteriores.

## Cómo armarlo (para quien lo integra al final)

1. Confirmar que `main` ya tiene mergeados `feature/ingestion`, `feature/rag`,
   `feature/agent` y `feature/prompts`.
2. Confirmar que `data/dataset.csv` está commiteado (sale de `/ingestion`).
3. Abrir esta notebook en Colab (`archivo > subir notebook` o clonando el repo).
4. Cargar `GOOGLE_API_KEY` y `TMDB_API_KEY` en los Secrets de Colab (ícono de llave).
5. Reemplazar la URL de `git clone` en la celda 1 por la del repo real del equipo.
6. Correr todas las celdas en orden y completar la sección 6 (casos de prueba) con
   corridas reales para mostrar en la defensa oral.

## Por qué desarrollo en .py y no directo en la notebook

Con 5 personas tocando el mismo notebook a la vez, cada commit genera conflictos de
merge en el JSON del `.ipynb` (los outputs de celda cambian el diff aunque el código no
cambie). Por eso el desarrollo real vive en módulos `.py` (`/ingestion`, `/rag`,
`/agent`, `/prompts`) que se pueden testear por separado, y esta notebook solo los
importa y orquesta al final.
