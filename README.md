# Recomendador grupal de películas y libros

TP2 de Sistemas Inteligentes — sistema de RAG + agente (Langchain + Gemini) que cruza
los gustos de 5 personas y devuelve una recomendación final justificada, en tono
canchero argentino.

Ver `docs/DISENO.md` para el detalle de todas las decisiones de diseño (qué se eligió
y por qué) — es material directo para la defensa oral.

## Arquitectura

```
ingestion/  →  data/dataset.csv  →  rag/  →  data/chroma/  →  agent/  →  respuesta final
  (TMDB,                                       (embeddings +    (usa
  Google Books)                                retriever)       prompts/)
```

| Carpeta | Qué hace | Quién la toca |
|---|---|---|
| `ingestion/` | Trae y limpia datos de TMDB + Google Books → `data/dataset.csv` | Persona 1 |
| `rag/` | Embeddings + ChromaDB, expone `retriever(query, k)` | Persona 2 |
| `agent/` | Carga perfiles, cruza gustos, llama al retriever, rankea | Persona 3 |
| `prompts/` | Personalidad "canchero argentino" del agente | Persona 4 |
| `notebook/` | Notebook final para Colab que integra todo | Persona 5 |
| `perfiles/` | Un `.json` por integrante con sus gustos | Los 5 |

Cada módulo se desarrolla y se prueba **solo**, sin depender de que los otros ya estén
terminados (ver el "Correr cada módulo por separado" de cada README).

## Instalación

Requiere Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Completar `.env` con:

- `GOOGLE_API_KEY` — gratis en https://aistudio.google.com/apikey
- `TMDB_API_KEY` — https://www.themoviedb.org/settings/api (gratis)
- `GOOGLE_BOOKS_API_KEY` — opcional, Google Books funciona sin key con rate limit bajo

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

## Cargar tu perfil

Copiar `perfiles/ejemplo_perfil.json` a `perfiles/<tu_nombre>.json` y completarlo. Ver
`perfiles/README.md` para el esquema completo.

## Armar el notebook final

El desarrollo se hace en módulos `.py` (para trabajar los 5 en paralelo sin pisarse en
un mismo `.ipynb`). El entregable final es `notebook/TP_recomendador_grupal.ipynb`,
que importa los 4 módulos y los corre en Colab. Instrucciones de armado en
`notebook/README.md`.

## Flujo de trabajo en git

`main` protegida. Una rama por módulo:

```
feature/ingestion
feature/rag
feature/agent
feature/prompts
feature/notebook
```

Cada quien mergea su rama a `main` vía Pull Request, con al menos 1 review de otro
integrante del equipo. Como cada rama toca una carpeta distinta, los conflictos de
merge deberían ser mínimos. El único paso secuencial real es `notebook/`, que se arma
al final una vez que las otras 4 ramas ya están en `main`.

## Estructura del repo

```
.
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── docs/
│   └── DISENO.md          # decisiones de diseño, material para la defensa
├── perfiles/
│   ├── ejemplo_perfil.json
│   └── README.md
├── ingestion/
│   ├── tmdb_client.py
│   ├── google_books_client.py
│   ├── clean.py
│   ├── schema.py
│   ├── build_dataset.py
│   └── README.md
├── rag/
│   ├── vectorstore.py
│   ├── retriever.py
│   └── README.md
├── agent/
│   ├── perfil.py
│   ├── ranking.py
│   ├── mediador.py
│   └── README.md
├── prompts/
│   ├── system_prompt.py
│   ├── ejemplos_tono.md
│   └── README.md
├── notebook/
│   ├── TP_recomendador_grupal.ipynb
│   └── README.md
└── data/                  # generado en runtime, no se commitea /chroma
    └── dataset.csv        # sí se commitea, para que el equipo no necesite las API keys
```
