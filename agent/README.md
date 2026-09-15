# agent/

El "agente mediador": carga los 5 perfiles, arma un criterio de búsqueda combinado,
llama a `rag.retriever`, rankea los candidatos según afinidad grupal y le pide la
recomendación final al LLM con el tono de `/prompts`.

## Setup

Necesita `GOOGLE_API_KEY` en el `.env` (gratis en https://aistudio.google.com/apikey),
y que `/rag` ya haya corrido
`python -m rag.vectorstore` al menos una vez (o sea, que exista `data/chroma/`).

## Correr

```bash
python -m agent.mediador
```

Esto carga automáticamente todos los `perfiles/*.json` que haya en el repo.

## Archivos

- `perfil.py`: `Perfil` (dataclass) + `cargar_perfil()` / `cargar_todos_los_perfiles()`.
  También `validar_generos_contra_dataset()`, que avisa géneros de perfiles que no
  existen en el dataset. Ver `perfiles/README.md` para el esquema del JSON.
- `ranking.py`: `rankear_candidatos(candidatos, perfiles)`, puntúa cada candidato de
  `rag.retriever` según cuántos perfiles lo bancan (géneros/títulos favoritos) vs.
  cuántos lo evitarían (géneros/títulos en "no_banca"), más el score semántico que trae
  el propio retriever. Ver los pesos y el diccionario de sinónimos de género al inicio
  del archivo si hay que ajustar la fórmula.
- `mediador.py`: `recomendar_grupal(perfiles=None)`, la función principal, ahora una
  chain LCEL con memoria (`RunnableWithMessageHistory`) en vez de un `llm.invoke()`
  suelto. Internamente:
  1. `construir_criterio_busqueda()` combina géneros/títulos de los 5 perfiles en una
     sola query de texto (sin "no_banca" ni `notas_libres`, ver el docstring del porqué).
  2. Llama a `rag.retriever(criterio, k=8)`.
  3. Rankea con `ranking.rankear_candidatos()` y se queda con el top 3.
  4. Le pasa perfiles + top 3 a la chain (Gemini + system prompt de `/prompts`) y
     devuelve la recomendación final en texto.

## Contrato con /notebook

`recomendar_grupal() -> {"recomendacion": str, "candidatos_rankeados": list[dict],
"criterio_busqueda": str}`.
