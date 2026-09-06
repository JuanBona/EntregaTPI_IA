# Decisiones de diseño

Documento de referencia para la defensa oral del TP ("Identificación de dificultades" /
"Documentación técnica" en la rúbrica). Explica qué se decidió y por qué.

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

El stack ya usa Claude (Anthropic) como LLM. Sumar OpenAI *solo* para embeddings agrega:
una API key más para gestionar entre 5 personas, un costo (aunque bajo) por llamada, y un
punto de falla extra el día de la defensa si no hay internet estable.

Se usa `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` vía
`langchain-huggingface`, corriendo local (CPU alcanza para el tamaño del dataset del TP):

- **Gratis y sin key**: no depende de cuota ni de que alguien pague.
- **Multilingüe**: las sinopsis de TMDB/Google Books vienen mezcladas en español e inglés,
  y los perfiles pueden tener títulos en idioma original (ej. "Prisoners" en vez de
  "Prisioneros") — el modelo multilingüe embebe bien ambos casos en el mismo espacio.
- **Trade-off aceptado**: calidad de embedding levemente menor que `text-embedding-3` de
  OpenAI o Voyage AI en inglés puro, y la primera corrida en Colab tarda un poco más porque
  descarga el modelo (~1 GB). Para el volumen de datos de este TP (cientos de ítems, no
  millones) esa diferencia no es perceptible en la calidad de las recomendaciones finales.
- **Alternativa considerada**: Voyage AI (partner recomendado por Anthropic, mejor calidad,
  free tier generoso) — se descartó por sumar una tercera dependencia de red/API key sin
  necesidad para el alcance del TP. Si el resultado con HuggingFace local no convence,
  migrar a Voyage es un cambio de una sola línea en `rag/vectorstore.py`.

## Esquema del perfil de usuario (`perfiles/*.json`)

Cada integrante carga su propio JSON (ver `perfiles/ejemplo_perfil.json`). Decisiones:

- `contenido_favorito` y `no_banca.titulos` son **listas mixtas** de películas y libros
  (el campo `tipo` es opcional por ítem) — no se fuerza a separar por tipo porque muchas
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

## Flujo de git

`main` protegida. Ramas por módulo: `feature/ingestion`, `feature/rag`, `feature/agent`,
`feature/prompts`, `feature/notebook`. Cada una mergea a `main` vía Pull Request con al
menos 1 review de otro integrante. Como cada rama toca solo su carpeta, los conflictos de
merge deberían ser mínimos o nulos — el único archivo compartido es `notebook/` que se
arma al final, integrando el trabajo ya mergeado de las otras 4 ramas.
