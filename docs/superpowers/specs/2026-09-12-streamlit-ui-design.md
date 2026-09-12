# Interfaz Streamlit para probar/demostrar el recomendador

## Contexto

El pipeline (`ingestion/` → `rag/` → `agent/` → `prompts/`) ya funciona de punta a
punta y su entregable formal es `notebook/TP_recomendador_grupal.ipynb` (Colab). Falta
una forma más cómoda de probarlo y de mostrarlo en la defensa oral sin depender de
Colab ni de editar `.json` a mano.

## Alcance

- Nuevo: `ui/app.py`, capa de interfaz sobre los módulos existentes. No se toca
  `notebook/`, que queda intacto como entregable separado.
- Corre local: `streamlit run ui/app.py`. No se despliega online.
- No reemplaza ni duplica lógica de `agent/`, `rag/` o `prompts/`: solo los importa.

## Diseño

**Estructura de la página:**
- 5 tabs, uno por integrante (`perfiles/*.json`, excluyendo `ejemplo_perfil.json`).
- Cada tab: formulario pre-cargado con los datos actuales del perfil —
  géneros favoritos (películas/libros) como multiselect + input libre para agregar
  géneros nuevos, contenido favorito y "no banca" como listas editables de texto,
  notas libres como text area. Botón "Guardar cambios" por tab → sobreescribe el
  `perfiles/<nombre>.json` correspondiente (mismo schema que `agent/perfil.py` ya
  espera, sin cambios al schema).
- Debajo de los tabs: botón "Generar recomendación grupal" → carga los 5 perfiles
  desde disco (ya con los últimos cambios guardados) y corre
  `agent.mediador.recomendar_grupal()`.
- Resultado mostrado en 3 bloques: criterio de búsqueda usado (texto chico/gris),
  tabla de candidatos rankeados (`st.dataframe`), recomendación final (markdown,
  bloque destacado).

**Manejo de errores:**
- Si falta `GOOGLE_API_KEY` en el entorno, mostrar un `st.error` con instrucciones
  (en vez de dejar que reviente el traceback de la librería).
- Si `data/chroma/` no existe todavía, construirlo on-demand la primera vez (mismo
  `construir_vectorstore()` que ya existe), mostrando un spinner mientras descarga el
  modelo de embeddings.

**Performance:**
- Vectorstore cacheado con `st.cache_resource` para no recargar el modelo de
  embeddings en cada rerun de Streamlit (cada click dispara un rerun completo del
  script, comportamiento normal de Streamlit).

## Fuera de alcance

- Deploy online (Streamlit Community Cloud) — no pedido, se decidió quedarse con uso
  local para la defensa.
- Cambios al schema de `perfiles/*.json` o a la lógica de `agent/`/`rag/`.
- Integración con la notebook de Colab — quedan como dos formas de correr el mismo
  pipeline, sin compartir código de UI entre sí.

## Testing

- Manual: correr `streamlit run ui/app.py` local, cargar los 5 perfiles reales,
  editar uno, guardar, generar recomendación, confirmar que el `.json` se actualizó
  en disco y que la recomendación referencia el cambio.
- Caso sin `GOOGLE_API_KEY`: confirmar que se ve el `st.error`, no un traceback.
