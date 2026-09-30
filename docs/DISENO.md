# Decisiones de diseño

Decisiones técnicas del proyecto y los problemas que fuimos encontrando.

## Arquitectura general

```
ingestion/  →  data/dataset.csv  →  rag/  →  data/chroma/  →  agent/  →  respuesta final
   (TMDB,                                      (retriever)      (usa
   Google Books)                                                prompts/)
```

5 módulos independientes, cada uno con su propio contrato de entrada/salida, para que las
5 personas del grupo trabajen en paralelo sin pisarse:

| Módulo | Responsable de | Depende de | Expone |
|---|---|---|---|
| `ingestion/` | Traer y limpiar datos de TMDB + Google Books | nada (solo APIs externas) | `data/dataset.csv` |
| `rag/` | Embeddings + ChromaDB | `data/dataset.csv` | `retriever(query, k)` |
| `agent/` | Cruzar 5 perfiles, armar criterio, rankear | `rag.retriever`, `perfiles/*.json` | `recomendar_grupal(perfiles)` |
| `prompts/` | Personalidad "canchero argentino" | nada | `SYSTEM_PROMPT`, `build_user_prompt()` |
| `notebook/` | Integrar todo para la entrega en Colab | los 4 anteriores | notebook ejecutable |

## Por qué embeddings locales (HuggingFace) y no OpenAI

El stack ya usa Gemini (Google) como LLM. Sumar OpenAI *solo* para embeddings agrega:
una API key más para gestionar entre 5 personas, un costo (aunque bajo) por llamada, y un
punto de falla extra si no hay internet estable.

Se usa `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` vía
`langchain-huggingface`, corriendo local (CPU alcanza para el tamaño del dataset del TP):

- **Gratis y sin key**: no depende de cuota ni de que alguien pague.
- **Multilingüe**: las sinopsis de TMDB/Google Books vienen mezcladas en español e inglés,
  y los perfiles pueden tener títulos en idioma original (ej. "Prisoners" en vez de
  "Prisioneros"), el modelo multilingüe embebe bien ambos casos en el mismo espacio.
- **Trade-off aceptado**: calidad de embedding levemente menor que `text-embedding-3` de
  OpenAI o Voyage AI en inglés puro, y la primera corrida en Colab tarda un poco más porque
  descarga el modelo (~1 GB). Para el volumen de datos de este TP (cientos de ítems, no
  millones) esa diferencia no es perceptible en la calidad de las recomendaciones finales.
- Se descartó Voyage AI por sumar otra dependencia de red y API key sin necesidad para el
  alcance del TP.

## Por qué LangChain como framework, y no como wrapper fino

La primera versión del agente hacía una sola llamada directa `llm.invoke(prompt_armado_a_mano)`,
sin usar nada propio de LangChain más que el cliente del modelo. Se cambió a una chain LCEL real
en `agent/mediador.py`:

```python
chain = prompt | _get_llm() | StrOutputParser()
chain_con_memoria = RunnableWithMessageHistory(
    chain, _historial, input_messages_key="mensaje", history_messages_key="historial"
)
```

- `prompt` es un `ChatPromptTemplate` (`prompts/system_prompt.py`) con `MessagesPlaceholder("historial")`,
  no un string armado con f-strings.
- `RunnableWithMessageHistory` le da memoria de conversación al agente: cada `session_id` tiene
  su propio historial en `InMemoryChatMessageHistory`, así que un `recomendar_grupal(..., mensaje="dame otra opción")`
  en la misma sesión tiene en cuenta lo que ya se recomendó antes.
- Se descartó armar un `AgentExecutor` con tools (ej. "tool de retriever", "tool de ranking")
  porque el flujo del TP es siempre el mismo (retriever -> ranking -> LLM), no hay que decidir
  dinámicamente qué paso usar. Una chain LCEL cubre el requisito de "usar LangChain como
  framework" sin la complejidad extra de un agente con tool-calling que no aporta nada acá.

## Por qué Google Gemini como LLM, y no Claude o GPT

El agente usó Anthropic al principio, pero se migró a Gemini (`gemini-3.6-flash`, vía
`langchain-google-genai`) por una razón simple para un grupo de 5 estudiantes: **es gratis**.
La API de Google AI Studio tiene un tier gratuito sin tarjeta (con un límite diario de
requests, suficiente para desarrollar y para la demo), mientras que Anthropic y OpenAI
requieren carga de saldo. Para el alcance de este TP el modelo puntual importa menos que
poder iterar y probar sin gastar dinero real entre 5 personas.

## Esquema del perfil de usuario (`perfiles/*.json`)

Cada integrante carga su propio JSON (ver `perfiles/ejemplo_perfil.json`). Decisiones:

- `contenido_favorito` y `no_banca.titulos` son **listas mixtas** de películas y libros
  (el campo `tipo` es opcional por ítem), no se fuerza a separar por tipo porque muchas
  veces el usuario no lo tiene claro o no le importa distinguir.
- Los títulos se guardan **tal cual el usuario los conoce**, en cualquier idioma (ej.
  "Prisoners" en vez de "Prisioneros"). El matching contra TMDB/Google Books en
  `agent/mediador.py` normaliza y busca por título sin asumir idioma.
- `generos_favoritos` sí se separa por tipo (`peliculas` / `libros`) porque las taxonomías
  de género de cine y de libros no son intercambiables (ej. "policial" es común en libros,
  "thriller" en cine, y no siempre son sinónimos).

## Esquema del dataset (`data/dataset.csv`)

Columnas: `id, tipo, titulo, sinopsis, generos, rating, anio, fuente, fuente_id,
autor_director, idioma`.

Se agregaron `id` (hash estable de `tipo+titulo+anio`, para deduplicar si se corre la
ingesta más de una vez), `fuente`/`fuente_id` (para poder rastrear un ítem raro hasta la
API original durante debugging) e `idioma`, además de las 6 columnas mínimas pedidas.

## Dificultades encontradas

Problemas detectados al probar el sistema con el dataset real, y cómo se resolvió cada uno:

- **Géneros que no matcheaban por tildes.** Los perfiles se tipean a mano sin tildes
  ("ciencia ficcion") pero el dataset viene de TMDB/Google Books con tildes ("Ciencia
  ficción"). Sin normalizar, 8 de 16 géneros de los perfiles nunca matcheaban nada.
  Se arregló normalizando con `unicodedata` en `agent/ranking.py`. Un segundo caso
  parecido: "thriller" (como lo tipea el grupo para cine) y "policial" (para libros) no
  existen así en el dataset, que usa "Suspense" y "Crimen"; se agregó un diccionario
  chico de sinónimos en el mismo módulo.
- **Las negaciones del perfil confundían la búsqueda semántica.** `notas_libres` a
  veces tiene negaciones ("no banco terror"), y los modelos de embeddings no manejan
  bien la negación: esa frase puede quedar semánticamente cerca de "terror" en vez de
  lejos. Se sacó `notas_libres` de la query que arma `agent/mediador.py` para el
  retriever; ahora esas negaciones solo llegan al prompt del LLM (que sí las entiende
  como texto).
- **El ranking ignoraba el score semántico del RAG.** `rag.retriever()` devuelve un
  `score` (distancia: más bajo, más parecido) por candidato, pero `agent/ranking.py`
  ordenaba solo por el match de géneros/rating, sin usarlo. Se sumó como un término más
  del score grupal.
- **`autor_director` vacío en las películas.** El endpoint que usa `ingestion/` para
  traer películas (`/discover/movie`) no incluye director, hace falta un pedido aparte
  por película. Se agregó un backfill (`ingestion/backfill_datos_faltantes.py`) que pide
  `/movie/{id}/credits` para cada película usando el `fuente_id` ya guardado.
  **Resuelto: las 178/178 películas tienen director real.**
- **Los libros quedaban con un solo género.** `ingestion/clean.py` etiquetaba cada
  libro únicamente con el género de la *búsqueda* que lo trajo de Google Books, no con
  sus categorías reales (`volumeInfo.categories`). Se agregó un backfill
  (`ingestion/backfill_datos_faltantes.py`) que pide `/volumes/{id}` por libro usando el
  `fuente_id` ya guardado, y solo agrega las categorías que matchean el vocabulario de
  géneros conocido del dataset (para no romper las comparaciones de `agent/ranking.py`
  con categorías en inglés sueltas). **Resuelto: 40/98 libros terminaron con un género
  extra** (los otros 58 solo tenían el género de búsqueda entre sus categorías reales de
  Google Books, así que no había nada más para agregar). Sin `GOOGLE_BOOKS_API_KEY` este
  backfill no funciona: el rate limit gratuito devuelve 429 para casi todos los requests,
  incluso con reintentos; hace falta una key propia (gratis, Google Cloud Console,
  habilitando la Books API).
- **El rating imputado de los libros (limitación aceptada, no arreglada).** Google
  Books no tiene `averageRating` para la mayoría de los libros que trae la búsqueda por
  tema; cuando falta, `ingestion/clean.py` imputa 6.0 para no romper el ranking. Es una
  limitación real de la fuente de datos (no hay rating que "arreglar", no existe), así
  que se documenta acá en vez de inventar un valor con más precisión falsa.
- **El embedding semántico también arrastra el problema de vocabulario.** Una query
  clara de libro como "novela policial nordica" trae mayoría de películas entre los
  resultados del retriever (4 de 5), porque el dataset etiqueta esas películas como
  "Crimen" y no "policial": el embedding tira para el lado de acción/crimen en general.
  El backfill de géneros de libros mejoró esto un poco (0/5 → 1/5 libros en el
  top), pero el fix de sinónimos de `agent/ranking.py` no lo toca, porque actúa
  *después* de la búsqueda semántica, no en el retriever. Queda como límite conocido
  del approach de embeddings genéricos para este volumen de datos.
