# Recomendador grupal de películas y libros

TP2 de Sistemas Inteligentes, sistema de RAG + agente (Langchain + Gemini) que cruza
los gustos de 5 personas y devuelve una recomendación final justificada.

Las decisiones de diseño están en `docs/DISENO.md`.

## Arquitectura

```
ingestion/  →  data/dataset.csv  →  rag/  →  data/chroma/  →  agent/  →  respuesta final
  (TMDB,                                       (embeddings +    (usa
  Google Books)                                retriever)       prompts/)
```

| Carpeta | Qué hace | Quién la toca |
|---|---|---|
| `ingestion/` | Trae y limpia datos de TMDB + Google Books → `data/dataset.csv` | Lucas |
| `rag/` | Embeddings + ChromaDB, expone `retriever(query, k)` | Rafa |
| `agent/` | Carga perfiles, cruza gustos, llama al retriever, rankea | Juan |
| `prompts/` | Personalidad "canchero argentino" del agente | Marcos |
| `notebook/` | Notebook final para Colab que integra todo | Bruno |
| `perfiles/` | Un `.json` por integrante con sus gustos | Los 5 |

Cada módulo se desarrolla y se prueba **solo**, sin depender de que los otros ya estén
terminados (ver el "Correr cada módulo por separado" de cada README).

## Cómo funciona el sistema, paso a paso

1. Cada integrante completa su perfil en `perfiles/<nombre>.json`: géneros favoritos
   (separados por película y libro), contenido que le gustó, géneros/títulos que no
   banca, y notas libres en texto natural. Ver `perfiles/README.md`.
2. `agent/mediador.py` (función `recomendar_grupal()`) arranca cargando todos los
   perfiles y arma **dos** criterios de búsqueda por separado, uno de película y otro
   de libro, combinando solo los géneros y títulos favoritos de ese tipo entre los 5
   (`construir_criterio_busqueda(perfiles, tipo)`). Están separados a propósito: con un
   único criterio mezclado, el vocabulario de películas (casi el doble de ítems que
   libros en el dataset) ahogaba al de libros y el retriever casi no traía libros entre
   los candidatos. Los "no banca" y las notas libres **no** entran acá a propósito: los
   modelos de embeddings no manejan bien la negación ("no me gusta terror" puede quedar
   cerca de "terror"), así que esas negaciones se dejan para después.
3. Cada criterio se manda a `rag.retriever(query, k, tipo)`, que busca por similitud
   semántica **dentro de ese tipo** (filtro `tipo=` sobre metadata) sobre los ~276
   ítems de `data/dataset.csv` (películas de TMDB + libros de Google Books) ya
   embeddeados en ChromaDB (`data/chroma/`, se genera local, no se commitea), y
   devuelve los `k` candidatos más parecidos de ese tipo.
4. `agent/ranking.py` reordena, por separado, los candidatos de cada tipo según qué
   tan bien le cierran a los 5 perfiles **juntos**: suma puntos por cada género
   favorito que matchea, resta por género o título que alguien no banca, y también
   pesa el rating y el score semántico que ya trajo el retriever (para no perder esa
   señal). Incluye un mapeo de sinónimos (ej. "thriller" ↔ "Suspense", "policial" ↔
   "Crimen") porque los perfiles y el dataset no siempre usan la misma palabra para lo
   mismo.
5. Los top candidatos rankeados de cada tipo, junto con el resumen de los 5 perfiles,
   se le pasan en una sola llamada a una chain de LangChain (`ChatPromptTemplate` de
   `prompts/system_prompt.py` + Gemini, con `RunnableWithMessageHistory` para tener
   memoria de conversación) que devuelve **dos** recomendaciones en el mismo texto, una
   de película y una de libro (separadas con encabezados `## Pelicula` / `## Libro` que
   `agent/mediador.py` después separa para mostrarlas en paneles distintos), cada una
   justificada, en tono argentino, sin inventar datos que no estén en perfiles o
   candidatos.
6. Todo esto se prueba módulo por módulo en `.py` (ver `tests/`), se puede probar
   interactivamente con la interfaz Streamlit (`ui/app.py`), y se integra al final en
   `notebook/TP_recomendador_grupal.ipynb`, el entregable para Colab.

## Instalación

Requiere Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Completar `.env` con:

- `GOOGLE_API_KEY`, gratis en https://aistudio.google.com/apikey
- `TMDB_API_KEY`, https://www.themoviedb.org/settings/api (gratis)
- `GOOGLE_BOOKS_API_KEY`, opcional, Google Books funciona sin key con rate limit bajo

## Correr cada módulo por separado

```bash
# 1. Ingesta (solo si no existe todavía data/dataset.csv, o para refrescarlo)
python -m ingestion.build_dataset

# 2. RAG: genera embeddings y los persiste en ChromaDB
python -m rag.vectorstore

# 3. Probar el retriever solo
python -c "from rag.retriever import retriever; print(retriever('thriller psicológico', k=3))"

# 4. Agente completo (necesita 1 y 2 ya corridos, y al menos un perfil en perfiles/)
python -m agent.mediador
```

Cada carpeta tiene su propio `README.md` con más detalle (setup, cómo correrla sola,
y el "contrato" de datos que expone al resto del pipeline).

## Interfaz de prueba/demo (Streamlit)

Para probar el sistema completo con una interfaz web local (editar perfiles + generar
recomendación con un click), sin usar Colab:

```bash
streamlit run ui/app.py
```

Abre automáticamente `http://localhost:8501` en el navegador. Necesita `GOOGLE_API_KEY`
en el `.env` (ver arriba) y que `data/dataset.csv` exista, el vectorstore se genera
solo la primera vez que se corre.

## Cargar tu perfil

Copiar `perfiles/ejemplo_perfil.json` a `perfiles/<tu_nombre>.json` y completarlo. Ver
`perfiles/README.md` para el esquema completo.

## Notebook

`notebook/TP_recomendador_grupal.ipynb` importa los módulos `.py` y corre todo el flujo
en Colab. Ver `notebook/README.md`.

## Estructura del repo

```
.
├── README.md                          # este archivo
├── requirements.txt                   # dependencias con versiones fijas
├── .env.example                       # plantilla de API keys y config (copiar a .env)
├── .gitignore
├── docs/
│   └── DISENO.md                      # decisiones de diseño
├── perfiles/
│   ├── ejemplo_perfil.json            # plantilla para copiar como perfiles/<nombre>.json
│   └── README.md                      # esquema de los campos del perfil
├── ingestion/
│   ├── tmdb_client.py                 # pega contra TMDB: películas y (backfill) director
│   ├── google_books_client.py         # pega contra Google Books: libros y (backfill) categorías
│   ├── clean.py                       # normaliza ambas fuentes al esquema común
│   ├── schema.py                      # columnas del dataset final y generador de id
│   ├── build_dataset.py               # orquesta la ingesta y escribe data/dataset.csv
│   ├── backfill_datos_faltantes.py    # completa director/géneros que la ingesta inicial no trae
│   └── README.md
├── rag/
│   ├── vectorstore.py                 # arma/carga los embeddings en ChromaDB
│   ├── retriever.py                   # retriever(query, k, tipo) que usa agent/
│   └── README.md
├── agent/
│   ├── perfil.py                      # dataclass Perfil, carga de perfiles/*.json, validación de géneros
│   ├── ranking.py                     # rankea candidatos según afinidad con los 5 perfiles
│   ├── mediador.py                    # recomendar_grupal(): orquesta todo el flujo (chain LCEL + memoria)
│   └── README.md
├── prompts/
│   ├── system_prompt.py               # personalidad del agente y el ChatPromptTemplate (LCEL)
│   └── README.md
├── notebook/
│   ├── TP_recomendador_grupal.ipynb   # entregable final para Colab
│   └── README.md
├── ui/
│   ├── app.py                         # interfaz Streamlit: editar perfiles y generar recomendación
│   ├── perfil_forms.py                # conversión perfil <-> formulario web
│   └── __init__.py
├── tests/
│   ├── agent/                         # tests de perfil.py y ranking.py
│   └── ui/                            # tests de perfil_forms.py
└── data/                              # generado en runtime, no se commitea /chroma
    └── dataset.csv                    # sí se commitea, para que el equipo no necesite las API keys
```
